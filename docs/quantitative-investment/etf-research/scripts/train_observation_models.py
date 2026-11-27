"""Freeze each registered paired ridge fit from verified pre-fold decisions and labels."""
import argparse
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import re

from observation_decision_status import decision_row
from observation_label_status import label_row
from observation_labels import CALENDAR, CALENDAR_SHA, label_window
from seal_observation_decision import first_archive
from etf_research.admission import sessions_between
from etf_research.evidence_archive import capture, verify as verify_archive
from etf_research.observation_decision_receipt import DECISIONS
from etf_research.observation_experiment import (
    BASE, MIN_TRAIN, VARIANTS, feature_vector, holdouts, label_floor, label_vector, ridge_fit,
)
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, encoded, inside, lock, read, seal, sha, sync_dir, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
LOG = 'reports/research-models'
TIMER = 'etf-research-model.timer'
CODE = (
    'PROTOCOL_OBSERVATION_V1.md', CALENDAR, 'config/research_observation.json',
    'deploy/etf-research-model.service', 'deploy/etf-research-model.timer',
    'scripts/train_observation_models.py', 'scripts/observation_decision_status.py',
    'scripts/observation_label_status.py','scripts/observation_labels.py',
    'scripts/seal_observation_decision.py','scripts/seal_observation_labels.py',
    'src/etf_research/observation_decision_receipt.py','src/etf_research/observation_experiment.py',
    'src/etf_research/admission.py','src/etf_research/evidence_archive.py','src/etf_research/publication.py',
)


def now():
    return datetime.now(timezone.utc)


def fold_cutoff(start):
    return datetime.combine(start,time(),TZ)


def describe_fold(origin, observed):
    if origin is None:
        return dict(status='observation_origin_pending',studyOrigin=None,fold=None)
    intervals = holdouts(date.fromisoformat(origin['date']))
    today = observed.astimezone(TZ).date()
    for start,end in intervals:
        if start<=today<end:
            return dict(status='fold_active',studyOrigin=origin,fold=dict(start=str(start),end=str(end)))
    if today<intervals[0][0]:
        return dict(status='training_accumulation',studyOrigin=origin,fold=None,
                    firstFoldStart=str(intervals[0][0]))
    return dict(status='observation_ended',studyOrigin=origin,fold=None)


def admitted_row(root, store, entry, window, origin, cutoff, observed):
    decision = decision_row(root,store,entry,cutoff,planned=True)
    if decision['status'] != 'eligible_inputs':
        return None, dict(reason='decision_'+decision['status'])
    record = decision['latest']
    sealed = instant(record['archivedAt'])
    if not instant(origin['archiveVerifiedAt'])<=sealed<=window.cutoff:
        return None, dict(reason='decision_time_outside_study')
    folder = inside(root,f'{DECISIONS}/{entry}/{record["id"]}')
    original = read(folder/'records/decision.json')['studyOrigin']
    if original!=origin:
        return None, dict(reason='different_study_origin')

    label = label_row(root,store,entry,cutoff,decision,details=True)
    if label['status']!='evidence_complete' or not instant(label['readyAt'])<cutoff:
        seen = label_row(root,store,entry,observed,decision,details=False)
        if seen['status']=='evidence_complete' and instant(seen['readyAt'])>=cutoff:
            return None, dict(reason='label_ready_after_fold_cutoff',labelReadyAt=seen['readyAt'],
                              labelArchiveSha256=seen['latest']['archiveSha256'])
        return None, dict(reason='label_'+label['status'])
    if instant(label['readyAt'])<label_floor(window):
        return None, dict(reason='label_precedes_fifth_close')

    cells = read(folder/'records/inputs.json')['cells']
    features = {name:feature_vector(cells, columns,window,sealed=sealed) for name,columns in VARIANTS.items()}
    if features['baseline'] is None:
        return None, dict(reason='baseline_inputs_not_ready')
    policy = cells.get('policyActiveCount')
    events = sorted(set(policy['eventIds'])) if features['policy'] is not None else []
    if features['policy'] is not None and (len(events)!=policy['value'] or any(not isinstance(e,str) for e in events)):
        return None, dict(reason='policy_count_or_event_ids_conflict')
    primary = label['latest']['results']['stock_bond_50_50']['base']
    returns, drawdown = label_vector(primary)
    if not (isfinite(returns) and 0<=drawdown<=1):
        return None, dict(reason='label_value_invalid')
    return dict(
        entryDay=str(entry),anchorDay=str(window.anchor),lastSession=str(window.last),
        inputSealedAt=record['archivedAt'],decisionArchiveSha256=record['archiveSha256'],
        decisionReceiptSha256=record['receiptSha256'], labelReadyAt=label['readyAt'],
        labelArchiveSha256=label['latest']['archiveSha256'],targets=[returns,drawdown],eventIds=events,
        vectors={name:list(values) if values is not None else None for name,values in features.items()},
    ),None


def build_cohort(root, store, origin, start, end, observed):
    cutoff = fold_cutoff(start)
    if observed<cutoff or (start,end) not in holdouts(date.fromisoformat(origin['date'])):
        raise ValueError('Model fit requires a registered fold and its elapsed training cutoff')
    calendar = root/CALENDAR
    if sha(calendar)!=CALENDAR_SHA:
        raise ValueError('Training calendar differs from verified exchange calendar')
    ranges = read(calendar)['holiday_ranges']
    scheduled = sessions_between(ranges,date.fromisoformat(origin['date']),start-timedelta(days=1))
    rows, exclusions = [], {}
    for entry in scheduled:
        window = label_window(root,entry)
        if window.last>=start:
            exclusions[str(entry)] = dict(reason='holding_window_crosses_fold',lastSession=str(window.last))
            continue
        try:
            row, exclusion = admitted_row(root,store,entry,window,origin,cutoff,observed)
        except (OSError,ValueError,KeyError,TypeError,ArithmeticError) as error:
            row, exclusion = None,dict(reason='training_evidence_invalid',errorType=type(error).__name__)
        if row is None:
            exclusions[str(entry)] = exclusion
        else:
            rows.append(row)
    return dict(schemaVersion=1,studyOrigin=origin,fold=dict(start=str(start),end=str(end)),
                observedAt=observed.isoformat(),trainingCutoff=cutoff.isoformat(),
                expectedTradingDays=len(scheduled),rows=rows,exclusions=exclusions)


def model_dict(columns, model):
    center,scale,intercept,weights = model
    return dict(columns=list(columns),center=center.tolist(),scale=scale.tolist(),
                intercept=intercept.tolist(),weights=weights.tolist())


def fit_comparisons(cohort):
    rows=cohort['rows']
    entries=[row['entryDay'] for row in rows]
    if entries!=sorted(set(entries)):
        raise ValueError('Training decisions must be unique and increasing')
    cutoff=instant(cohort['trainingCutoff'])
    start=date.fromisoformat(cohort['fold']['start'])
    end=date.fromisoformat(cohort['fold']['end'])
    origin=instant(cohort['studyOrigin']['archiveVerifiedAt'])
    registered=holdouts(origin.astimezone(TZ).date())
    if (start,end) not in registered or cutoff!=fold_cutoff(start):
        raise ValueError('Cohort is bound to a different experiment fold')
    if any(not row['entryDay']<=row['lastSession']<str(start) or
           not origin<=instant(row['inputSealedAt'])<instant(row['labelReadyAt'])<cutoff or
           instant(row['labelReadyAt'])<datetime.combine(date.fromisoformat(row['lastSession']),time(16),TZ)
           for row in rows):
        raise ValueError('Cohort contains a late or cross-fold training row')
    comparisons={}
    for variant,columns in VARIANTS.items():
        if variant=='baseline':
            continue
        matched=[row for row in rows if row['vectors'][variant] is not None]
        spec=dict(status='insufficient_training',trainingDays=len(matched),
                  trainingEntries=[row['entryDay'] for row in matched],
                  trainingEventIds=sorted({event for row in matched for event in row['eventIds']})
                                   if 'policyActiveCount' in columns else [],
                  missingVariantDays=len(rows)-len(matched),minimumTrainingDays=MIN_TRAIN)
        if len(matched)>=MIN_TRAIN:
            expanded = [row['vectors'][variant] for row in matched]
            base = [row['vectors']['baseline'] for row in matched]
            if any(len(x)!=len(columns) or len(y)!=len(BASE) or x[:len(BASE)]!=y
                   for x,y in zip(expanded,base,strict=True)):
                raise ValueError('Baseline and expanded inputs do not refer to equal price features')
            target = [row['targets'] for row in matched]
            models=dict(baseline=model_dict(BASE,ridge_fit(base,target)),
                        expanded=model_dict(columns,ridge_fit(expanded,target)))
            spec.update(status='fitted',models=models,modelSha256=sha256(encoded(models)).hexdigest())
        comparisons[variant]=spec
    return comparisons


def verify_model(root, store, folder, *, observed=None):
    observed = now() if observed is None else observed
    folder=folder.resolve()
    records=folder/'records'
    verify_bundle(records)
    receipt=read(folder/'receipt.json')
    packet=read(records/'training.json')
    cohort=packet['cohort']
    archive=verify_archive(store,receipt['archiveSha256'])
    names={path.relative_to(root).as_posix():sha(path) for path in records.iterdir()}
    hashes={**packet['codeSha256'],**names}
    sealed=instant(receipt['modelSealedAt'])
    if (folder.parent.parent!=root/LOG or folder.parent.name!=cohort['fold']['start']
            or packet['unit']!=TIMER or packet['invocation']!=folder.name or not re.fullmatch('[a-f0-9]{32}',folder.name)
            or receipt['path']!=folder.relative_to(root).as_posix()
            or receipt['manifestSha256']!=sha(records/'manifest.json')
            or not instant(cohort['trainingCutoff'])<=instant(cohort['observedAt'])<=instant(packet['computedAt'])
                <=instant(archive['created_at_utc'])<=sealed<=observed
            or set(archive['files'])!=set(hashes)
            or any(archive['files'][name]['sha256']!=digest for name,digest in hashes.items())
            or packet['comparisons']!=fit_comparisons(cohort)):
        raise ValueError('Model archive or paired fit verification failed')
    return receipt,packet


def archive_model(root, store, invocation, cohort):
    folder=root/LOG/cohort['fold']['start']/invocation
    records=folder/'records'
    records.mkdir(parents=True,exist_ok=False)
    bindings={name:sha(root/name) for name in CODE}
    comparisons=fit_comparisons(cohort)
    create(records/'training.json',dict(schemaVersion=1,unit=TIMER,invocation=invocation,
                    cohort=cohort,comparisons=comparisons,computedAt=now().isoformat(),codeSha256=bindings))
    seal(records)
    archive=capture(root,store,[p.relative_to(root).as_posix() for p in records.iterdir()]+list(bindings))
    verify_archive(store,archive['snapshot'])
    create(folder/'receipt.json',dict(schemaVersion=1,path=folder.relative_to(root).as_posix(),
                manifestSha256=sha(records/'manifest.json'),archiveSha256=archive['snapshot'],
                modelSealedAt=now().isoformat()))
    for path in (folder,folder.parent,folder.parent.parent):
        sync_dir(path)
    return verify_model(root,store,folder)


def status(root, store, observed):
    plan=dict(describe_fold(first_archive(root,store,observed),observed),observedAt=observed.isoformat())
    if not plan['fold']:
        return plan
    candidates=[]
    for receipt in (root/LOG/plan['fold']['start']).glob('*/receipt.json'):
        if instant(read(receipt)['modelSealedAt'])<=observed:
            result=verify_model(root,store,receipt.parent,observed=observed)
            if result[1]['cohort']['studyOrigin']!=plan['studyOrigin']:
                raise ValueError('Sealed fold belongs to a different study origin')
            candidates.append(result)
    if candidates:
        receipt,packet=min(candidates,key=lambda item:instant(item[0]['modelSealedAt']))
        plan.update(modelReceipt=receipt,comparisons={name:dict(status=fit['status'],trainingDays=fit['trainingDays'])
                                                        for name,fit in packet['comparisons'].items()})
    return plan


def run(root, store):
    invocation=os.environ.get('INVOCATION_ID','')
    if os.environ.get('TRIGGER_UNIT')!=TIMER or not re.fullmatch('[a-f0-9]{32}',invocation):
        raise ValueError('Model sealing requires its systemd timer')
    with lock(root/'.runtime/research-model.lock'):
        observed=now()
        plan=status(root,store,observed)
        if not plan['fold'] or 'modelReceipt' in plan:
            return plan
        start,end=(date.fromisoformat(plan['fold'][key]) for key in ('start','end'))
        try:
            cohort=build_cohort(root,store,plan['studyOrigin'],start,end,observed)
        except ValueError as error:
            if 'Calendar year lacks independent evidence' not in str(error):
                raise
            return dict(plan,status='calendar_unverified')
        archive_model(root,store,invocation,cohort)
        return status(root,store,now())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run',action='store_true')
    mode.add_argument('--status',action='store_true')
    mode.add_argument('--verify',type=Path)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--archive-store',type=Path,required=True)
    args=parser.parse_args()
    root,store=args.observation_root.resolve(),args.archive_store.resolve()
    if args.verify:
        receipt,packet=verify_model(root,store,args.verify)
        result=dict(receipt,trainingDays={key:value['trainingDays'] for key,value in packet['comparisons'].items()})
    else:
        result=status(root,store,now()) if args.status else run(root,store)
    print(json.dumps(result,ensure_ascii=False))
