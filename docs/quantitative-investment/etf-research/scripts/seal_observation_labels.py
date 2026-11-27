"""Schedule and verify five-session research labels tied to actual decision receipts."""
import argparse
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re

from observation_labels import EVIDENCE_ERRORS, assemble_label, label_window
from etf_research.evidence_archive import capture, verify as verify_archive
from etf_research.observation_decision_receipt import DECISIONS, verify_decision
from etf_research.observation_experiment import label_floor
from etf_research.policy_events import instant
from etf_research.publication import create, lock, read, seal, sha, sync_dir, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
LOG = 'reports/research-labels'
TIMER = 'etf-research-label.timer'
MAX_PER_RUN = 5
BINDINGS = (
    'PROTOCOL_OBSERVATION_V1.md', 'scripts/seal_observation_labels.py', 'scripts/observation_labels.py',
    'scripts/observe_opening_quotes.py','scripts/observation_price_inputs.py',
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
    bindings={name:sha(root/name) for name in BINDINGS}
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


def pending_windows(root, prices, store, checked_at):
    waiting, issues = [], []
    for folder in sorted((root/DECISIONS).glob('*')):
        try:
            entry=date.fromisoformat(folder.name)
            ready = label_floor(label_window(prices,entry))
            if checked_at<ready:
                continue
            decision=None
            for path in sorted(folder.glob('*/receipt.json')):
                verified=verify_decision(root,store,path.parent,observed=checked_at)
                if verified['status']=='eligible_inputs':
                    decision=path.parent
                    break
            if decision is None:
                continue
            previous=(root/LOG/folder.name)
            attempts=sorted(previous.glob('*/receipt.json'))
            if any(check_label(root,store,path.parent)['status']=='evidence_complete' for path in attempts):
                continue
            waiting.append((len(attempts),entry,decision))
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
