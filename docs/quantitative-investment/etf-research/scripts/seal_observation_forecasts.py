"""Write registered holdout forecasts before 08:55 using only frozen inputs and models."""
import argparse
from datetime import date, datetime, time, timedelta, timezone
import json
import os
from pathlib import Path
import re
from time import sleep

from observation_decision_status import decision_row
from observation_labels import CALENDAR, EVIDENCE_ERRORS, label_window
from train_observation_models import status as model_status, verify_model
from etf_research.admission import sessions_between
from etf_research.exchange_calendar import LOADER, calendar_at
from etf_research.evidence_archive import capture, verify as verify_archive
from etf_research.observation_decision_receipt import DECISIONS, deadline, verify_decision
from etf_research.observation_experiment import BASE, VARIANTS, feature_vector, ridge_predict
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, inside, lock, read, seal, sha, sync_dir, verify_bundle

ROOT=Path(__file__).resolve().parents[1]
LOG='reports/research-forecasts'
TIMER='etf-research-forecast.timer'
START=time(8,53)
POLL_UNTIL=time(8,54,20)
CODE=(
    LOADER,
    'PROTOCOL_OBSERVATION_V1.md', CALENDAR, 'deploy/etf-research-forecast.timer',
    'deploy/etf-research-forecast.service','scripts/seal_observation_forecasts.py',
    'scripts/train_observation_models.py','scripts/observation_decision_status.py',
    'src/etf_research/observation_decision_receipt.py','src/etf_research/observation_experiment.py',
    'src/etf_research/evidence_archive.py','src/etf_research/publication.py',
)


def now():
    return datetime.now(timezone.utc)


def trigger_from(env):
    name=env.get('TRIGGER_UNIT')
    invocation=env.get('INVOCATION_ID','')
    micros=env.get('TRIGGER_TIMER_REALTIME_USEC','')
    if name!=TIMER or not re.fullmatch('[a-f0-9]{32}',invocation) or not micros.isdecimal():
        raise ValueError('Forecast production requires its scheduled timer')
    return dict(unit=name,id=invocation,triggeredAt=datetime.fromtimestamp(int(micros)/1_000_000,timezone.utc).isoformat())


def forecast_outcome(packet, ready_at):
    day=date.fromisoformat(packet['entryDay'])
    started,finished=map(instant,(packet['startedAt'],packet['computedAt']))
    trigger=packet['trigger']
    activated=instant(trigger['triggeredAt'])
    if not datetime.combine(day,START,TZ)<=activated<=started<=finished<=ready_at<=deadline(day):
        return 'missed_deadline'
    return 'sealed_predictions' if any(row['status']=='predicted' for row in packet['comparisons'].values()) else 'no_prediction'


def compare_model(fit,variant,vector):
    result={}
    for name,columns in (('baseline',BASE),('expanded',VARIANTS[variant])):
        model=fit['models'][name]
        if model['columns']!=list(columns):
            raise ValueError('Forecast columns differ from the registered comparison')
        parameters=tuple(model[key] for key in ('center','scale','intercept','weights'))
        result[name]=ridge_predict(parameters,[vector[:len(columns)]])[0].tolist()
    return result


def forecast_comparisons(fits,cells,window,inputs_at,prior_events):
    result={}
    policy=cells.get('policyActiveCount')
    for variant,fit in fits.items():
        if fit['status']!='fitted':
            result[variant]=dict(status='insufficient_training',trainingDays=fit['trainingDays'])
            continue
        features=feature_vector(cells,VARIANTS[variant],window,sealed=inputs_at)
        if features is None:
            result[variant]=dict(status='inputs_missing')
            continue
        uses_policy='policyActiveCount' in VARIANTS[variant]
        events=sorted(set(policy['eventIds'])) if uses_policy else []
        if uses_policy and len(events)!=policy['value']:
            raise ValueError('Forecast policy count differs from event identity')
        overlap=sorted(set(events)&(set(fit['trainingEventIds'])|set(prior_events.get(variant,()))))
        if overlap:
            result[variant]=dict(status='policy_event_previously_seen',eventIds=overlap)
            continue
        result[variant]=dict(status='predicted',eventIds=events,modelSha256=fit['modelSha256'],
                             **compare_model(fit,variant,features))
    return result


def verify_forecast(root,store,folder,*,observed=None):
    observed=now() if observed is None else observed
    folder=folder.resolve()
    records=folder/'records'
    verify_bundle(records)
    receipt=read(folder/'receipt.json')
    packet=read(records/'forecast.json')
    archive=verify_archive(store,receipt['archiveSha256'])
    ready=instant(receipt['forecastSealedAt'])
    files={path.relative_to(root).as_posix():sha(path) for path in records.iterdir()}
    hashes={**files,**packet['codeSha256']}
    if (folder.parent.parent!=root/LOG or folder.parent.name!=packet['entryDay']
            or packet['trigger']['unit']!=TIMER or packet['trigger']['id']!=folder.name
            or not re.fullmatch('[a-f0-9]{32}',folder.name)
            or receipt['path']!=folder.relative_to(root).as_posix()
            or receipt['manifestSha256']!=sha(records/'manifest.json')
            or receipt['status']!=forecast_outcome(packet,ready)
            or not instant(packet['startedAt'])<=instant(packet['computedAt'])<=instant(archive['created_at_utc'])<=ready<=observed
            or set(archive['files'])!=set(hashes)
            or any(archive['files'][name]['sha256']!=digest for name,digest in hashes.items())):
        raise ValueError('Forecast archive or timeline verification failed')
    if receipt['status']=='sealed_predictions':
        decision,model=packet['decision'],packet['model']
        if not (decision and model and
                max(instant(decision['sealedAt']),instant(model['sealedAt']))<=instant(packet['computedAt'])):
            raise ValueError('Forecast used input or model before it was sealed')
    return receipt,packet


def previous_events(root,store,fold,observed,origin):
    events={variant:set() for variant in ('policy','combined')}
    for path in (root/LOG).glob('*/*/receipt.json'):
        entry=path.parent.parent.name
        if entry>=fold or not path.is_file():
            continue
        raw=read(path)
        if raw['status']!='sealed_predictions' or instant(raw['forecastSealedAt'])>observed:
            continue
        _,packet=verify_forecast(root,store,path.parent,observed=observed)
        if packet['studyOrigin']!=origin:
            continue
        for variant in events:
            row=packet['comparisons'].get(variant,{})
            if row.get('status')=='predicted':
                events[variant].update(row['eventIds'])
    return events


def archive_forecast(root,store,packet):
    folder=root/LOG/packet['entryDay']/packet['trigger']['id']
    records=folder/'records'
    records.mkdir(parents=True,exist_ok=False)
    calendar = calendar_at(root,instant(packet['startedAt']))
    bindings={relative:sha(root/relative) for relative in (*CODE,*calendar.extensions)}
    create(records/'forecast.json',dict(packet,codeSha256=bindings))
    seal(records)
    stored=capture(root,store,[p.relative_to(root).as_posix() for p in records.iterdir()]+list(bindings))
    verify_archive(store,stored['snapshot'])
    ready=now()
    receipt=dict(path=folder.relative_to(root).as_posix(),archiveSha256=stored['snapshot'],
                 manifestSha256=sha(records/'manifest.json'),forecastSealedAt=ready.isoformat(),
                 status=forecast_outcome(packet,ready))
    create(folder/'receipt.json',receipt)
    for directory in (folder,folder.parent,folder.parent.parent):
        sync_dir(directory)
    return verify_forecast(root,store,folder)[0]


def wait_for_decision(root,store,day):
    end=datetime.combine(day,POLL_UNTIL,TZ)
    while True:
        observed=now()
        decision=decision_row(root,store,day,observed,planned=True)
        if decision['status'] not in ('pending','pending_archive') or observed>=end:
            return decision,observed
        sleep(2)


def run(root,store):
    trigger=trigger_from(os.environ)
    started=now()
    day=started.astimezone(TZ).date()
    plan=model_status(root,store,started)
    if not plan['fold']:
        return dict(status=plan['status'],entryDay=str(day))
    calendar=calendar_at(root,started)
    if not sessions_between(calendar.ranges,day,day):
        return dict(status='not_scheduled',entryDay=str(day))
    with lock(root/'.runtime/research-forecast.lock'):
        folder=root/LOG/str(day)
        for path in sorted(folder.glob('*/receipt.json')):
            receipt,_=verify_forecast(root,store,path.parent)
            if receipt['status']=='sealed_predictions':
                return receipt
        packet=dict(schemaVersion=1,entryDay=str(day),trigger=trigger,startedAt=started.isoformat(),
                    studyOrigin=plan['studyOrigin'],fold=plan['fold'],decision=None,model=None,
                    comparisons={},sessions=[],reason=None)
        if not datetime.combine(day,START,TZ)<=instant(trigger['triggeredAt'])<=started<=deadline(day):
            packet['reason']='outside_scheduled_cutoff'
        else:
            try:
                window=label_window(root,day,started)
                if window.last>=date.fromisoformat(plan['fold']['end']):
                    packet['reason']='holding_window_crosses_fold'
                elif 'modelReceipt' not in plan:
                    packet['reason']='model_not_ready'
                else:
                    model=plan['modelReceipt']
                    _,bundle=verify_model(root,store,inside(root,model['path']),observed=started)
                    decision,observed=wait_for_decision(root,store,day)
                    if decision['status']!='eligible_inputs':
                        packet['reason']='decision_'+decision['status']
                    else:
                        item=decision['latest']
                        records=inside(root,f'{DECISIONS}/{day}/{item["id"]}')/'records'
                        if read(records/'decision.json')['studyOrigin']!=plan['studyOrigin']:
                            raise ValueError('Decision belongs to a different study origin')
                        cells=read(records/'inputs.json')['cells']
                        prior=previous_events(root,store,plan['fold']['start'],observed,plan['studyOrigin'])
                        packet.update(sessions=[str(session) for session in window.sessions],
                              decision=dict(path=records.parent.relative_to(root).as_posix(),
                                            receiptSha256=item['receiptSha256'],archiveSha256=item['archiveSha256'],
                                            sealedAt=item['archivedAt']),
                              model=dict(path=model['path'],archiveSha256=model['archiveSha256'],sealedAt=model['modelSealedAt']),
                              comparisons=forecast_comparisons(bundle['comparisons'],cells,window,
                                                               instant(item['archivedAt']),prior))
            except EVIDENCE_ERRORS as error:
                packet['reason']='evidence_unavailable'
                packet['diagnostic']=str(error)[:240]
        packet['computedAt']=now().isoformat()
        return archive_forecast(root,store,packet)


def reproduce_forecast(root,store,folder):
    receipt,packet=verify_forecast(root,store,folder)
    if receipt['status']!='sealed_predictions':
        return receipt
    entry=date.fromisoformat(packet['entryDay'])
    used_at=instant(packet['computedAt'])
    decision,model=packet['decision'],packet['model']
    decision_folder=inside(root,decision['path'])
    actual=verify_decision(root,store,decision_folder,observed=used_at)
    model_receipt,bundle=verify_model(root,store,inside(root,model['path']),observed=used_at)
    window=label_window(root,entry,instant(packet['startedAt']))
    if (actual['status']!='eligible_inputs' or actual['entryDay']!=str(entry)
            or sha(decision_folder/'receipt.json')!=decision['receiptSha256']
            or actual['archiveSha256']!=decision['archiveSha256'] or actual['archiveVerifiedAt']!=decision['sealedAt']
            or model_receipt['archiveSha256']!=model['archiveSha256'] or model_receipt['modelSealedAt']!=model['sealedAt']
            or packet['fold']!=bundle['cohort']['fold'] or packet['studyOrigin']!=bundle['cohort']['studyOrigin']
            or packet['sessions']!=[str(day) for day in window.sessions]
            or not date.fromisoformat(packet['fold']['start'])<=entry<=window.last<date.fromisoformat(packet['fold']['end'])):
        raise ValueError('Forecast inputs do not match the sealed decision and model')
    prior=previous_events(root,store,packet['fold']['start'],used_at,packet['studyOrigin'])
    cells=read(decision_folder/'records/inputs.json')['cells']
    calculated=forecast_comparisons(bundle['comparisons'],cells,window,instant(decision['sealedAt']),prior)
    if calculated!=packet['comparisons']:
        raise ValueError('Sealed forecast did not reproduce')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    method=parser.add_mutually_exclusive_group(required=True)
    method.add_argument('--run',action='store_true')
    method.add_argument('--verify',type=Path)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--archive-store',type=Path,required=True)
    args=parser.parse_args()
    root,store=args.observation_root.resolve(),args.archive_store.resolve()
    result=reproduce_forecast(root,store,args.verify) if args.verify else run(root,store)
    print(json.dumps(result,ensure_ascii=False))
