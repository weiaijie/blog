"""Schedule and verify five-session research labels tied to actual decision receipts."""
import argparse
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re

from observation_decision_status import decision_row
from observation_labels import EVIDENCE_ERRORS, assemble_label, label_window
from etf_research.exchange_calendar import LOADER, calendar_at
from etf_research.evidence_archive import capture, verify as verify_archive
from etf_research.observation_decision_receipt import DECISIONS
from etf_research.observation_experiment import label_floor
from etf_research.policy_events import instant
from etf_research.publication import create, lock, read, seal, sha, sync_dir, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
LOG = 'reports/research-labels'
TIMER = 'etf-research-label.timer'
MAX_PER_RUN = 5
BINDINGS = (
    LOADER,
    'PROTOCOL_OBSERVATION_V1.md', 'scripts/seal_observation_labels.py', 'scripts/observation_labels.py',
    'scripts/observe_opening_quotes.py','scripts/observation_price_inputs.py',
    'scripts/observation_decision_status.py',
    'deploy/etf-research-label.timer', 'deploy/etf-research-label.service',
    'scripts/audit_official_close.py','src/etf_research/observation_experiment.py',
    'src/etf_research/observation_decision_receipt.py','src/etf_research/admission.py',
    'src/etf_research/data.py','src/etf_research/official_history.py',
    'src/etf_research/accounting.py','src/etf_research/baselines.py',
    'data/snapshots/2026-11-04-calendar-08/calendar.json',
)


def now():
    return datetime.now(timezone.utc)


def live_identity(env):
    invocation=env.get('INVOCATION_ID','')
    if env.get('TRIGGER_UNIT')!=TIMER or not re.fullmatch('[a-f0-9]{32}',invocation):
        raise ValueError('Label production requires the independent systemd timer')
    return invocation


def verified_label(root, store, folder, *, observed=None):
    observed = now() if observed is None else observed
    folder=folder.resolve()
    records=folder/'records'
    verify_bundle(records)
    receipt=read(folder/'receipt.json')
    packet=read(records/'label.json')
    archived=verify_archive(store,receipt['archiveSha256'])
    ready=instant(receipt['archiveVerifiedAt'])
    names={p.relative_to(root).as_posix():sha(p) for p in records.iterdir()}
    hashes={**names,**packet['codeSha256']}
    payload=packet['payload']
    if (folder.parent.parent!=root/LOG or folder.name!=packet['invocation']
            or not re.fullmatch('[a-f0-9]{32}',folder.name) or packet['timer']!=TIMER
            or receipt['path']!=folder.relative_to(root).as_posix()
            or receipt['manifestSha256']!=sha(records/'manifest.json')
            or folder.parent.name!=payload['entryDay'] or payload['mode']!='scheduled_candidate'
            or payload['decision'] is None or payload['status'] not in ('evidence_complete','evidence_missing')
            or (payload['labels'] is not None)!=(payload['status']=='evidence_complete')
            or receipt['status']!=payload['status']
            or receipt['labelReadyAt']!=(receipt['archiveVerifiedAt'] if payload['labels'] is not None else None)
            or not instant(payload['notBefore'])<=instant(payload['observedAt'])<=instant(packet['computedAt'])
                <=instant(archived['created_at_utc'])<=ready<=observed
            or set(archived['files'])!=set(hashes)
            or any(archived['files'][name]['sha256']!=digest for name,digest in hashes.items())):
        raise ValueError('Label receipt or archived record does not match')
    return dict(receipt,entryDay=payload['entryDay'],gaps=payload['gaps']),payload


def check_label(root, store, folder):
    receipt,_ = verified_label(root,store,folder)
    return receipt


def archive_label(root, store, invocation, payload):
    folder=root/LOG/payload['entryDay']/invocation
    records=folder/'records'
    records.mkdir(parents=True,exist_ok=False)
    available = calendar_at(root,instant(payload['observedAt']))
    bindings={name:sha(root/name) for name in (*BINDINGS,*available.extensions)}
    create(records/'label.json',dict(schemaVersion=1,invocation=invocation,timer=TIMER,
                                    computedAt=now().isoformat(),codeSha256=bindings,payload=payload))
    seal(records)
    names=[p.relative_to(root).as_posix() for p in records.iterdir()] + list(bindings)
    archive=capture(root,store,names)
    verify_archive(store,archive['snapshot'])
    checked_at=now().isoformat()
    receipt=dict(path=folder.relative_to(root).as_posix(),manifestSha256=sha(records/'manifest.json'),
                 archiveSha256=archive['snapshot'],archiveVerifiedAt=checked_at,status=payload['status'],
                 labelReadyAt=checked_at if payload['labels'] is not None else None)
    create(folder/'receipt.json',receipt)
    for path in (folder,folder.parent,folder.parent.parent):
        sync_dir(path)
    return check_label(root,store,folder)


def check_label_binding(payload, window, decision):
    binding = payload['decision']
    expected = f"{DECISIONS}/{window.entry}/{decision['id']}"
    if (binding['path']!=expected or binding['archiveSha256']!=decision['archiveSha256']
            or binding['receiptSha256']!=decision['receiptSha256']
            or payload['sessions']!=[str(day) for day in window.sessions]
            or payload['anchorDay']!=str(window.anchor) or payload['lastSession']!=str(window.last)
            or instant(payload['notBefore'])!=label_floor(window)):
        raise ValueError('Label belongs to a different decision or trading window')


def pending_windows(root, prices, store, checked_at):
    waiting, issues = [], []
    for folder in sorted((root/DECISIONS).glob('*')):
        try:
            entry=date.fromisoformat(folder.name)
            window = label_window(prices,entry,checked_at)
            if checked_at<label_floor(window):
                continue
            day = decision_row(root,store,entry,checked_at,planned=True)
            for attempt in day['attempts']:
                if attempt['status']=='unverified':
                    issues.append(dict(entryDay=str(entry),decisionAttempt=attempt['id'],
                                       reason='Decision archive did not verify'))
            if day['status']!='eligible_inputs':
                continue
            selected = day['latest']
            complete, checked = False,0
            for path in sorted((root/LOG/str(entry)).glob('*/receipt.json')):
                try:
                    if instant(read(path)['archiveVerifiedAt'])>checked_at:
                        continue
                    checked += 1
                    receipt,payload = verified_label(root,store,path.parent,observed=checked_at)
                    check_label_binding(payload,window,selected)
                    complete |= receipt['status']=='evidence_complete'
                except EVIDENCE_ERRORS as error:
                    issues.append(dict(entryDay=str(entry),labelAttempt=path.parent.name,reason=str(error)[:350]))
            if not complete:
                waiting.append((checked,entry,folder/selected['id']))
        except EVIDENCE_ERRORS as error:
            issues.append(dict(entryDay=folder.name,reason=str(error)[:350]))
    return sorted(waiting),issues


def run(root, prices, store):
    invocation=live_identity(os.environ)
    with lock(root/'.runtime/research-label.lock'):
        asof=now()
        waiting,issues=pending_windows(root,prices,store,asof)
        results=[]
        for _,entry,folder in waiting[:MAX_PER_RUN]:
            try:
                payload=assemble_label(prices,root,store,entry,now(),decision_folder=folder)
                results.append(archive_label(root,store,invocation,payload))
            except EVIDENCE_ERRORS as error:
                issues.append(dict(entryDay=str(entry),reason=str(error)[:350]))
        return dict(observedAt=asof.isoformat(),due=len(waiting),results=results,issues=issues)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--run',action='store_true')
    action.add_argument('--verify',type=Path)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--price-project',type=Path)
    parser.add_argument('--archive-store',type=Path,required=True)
    args=parser.parse_args()
    root,store=args.observation_root.resolve(),args.archive_store.resolve()
    if args.verify:
        result=check_label(root,store,args.verify)
    elif args.price_project is None:
        parser.error('--price-project is required to produce labels')
    else:
        result=run(root,args.price_project.resolve(),store)
    print(json.dumps(result,ensure_ascii=False))
