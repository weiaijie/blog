"""Persist each dated evaluation report with its actual verification time."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from observation_labels import CALENDAR
from etf_research.evidence_archive import capture, verify as verify_archive
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, lock, read, seal, sha, sync_dir, verify_bundle

ROOT=Path(__file__).resolve().parents[1]
LOG='reports/research-evaluation'
TIMER='etf-research-evaluation.timer'
CODE=(
    'PROTOCOL_OBSERVATION_V1.md', CALENDAR, 'config/research_observation.json',
    'deploy/etf-research-evaluation.service','deploy/etf-research-evaluation.timer',
    'scripts/seal_observation_evaluation.py','scripts/observation_out_of_sample.py',
    'scripts/observation_status.py','scripts/observation_decision_status.py',
    'scripts/observation_forecast_status.py','scripts/observation_label_status.py',
    'scripts/seal_observation_forecasts.py','scripts/seal_observation_labels.py',
    'scripts/train_observation_models.py','scripts/observation_labels.py',
    'src/etf_research/observation_experiment.py','src/etf_research/evidence_archive.py',
)


def now():
    return datetime.now(timezone.utc)


def verify_evaluation(root,store,folder,*,observed=None):
    observed=now() if observed is None else observed
    folder=folder.resolve()
    records=folder/'records'
    verify_bundle(records)
    receipt=read(folder/'receipt.json')
    packet=read(records/'evaluation.json')
    archive=verify_archive(store,receipt['archiveSha256'])
    report=packet['report']
    as_of=instant(report['asOf'])
    names={path.relative_to(root).as_posix():sha(path) for path in records.iterdir()}
    hashes={**names,**packet['codeSha256']}
    if (folder.parent.parent!=root/LOG or folder.parent.name!=str(as_of.astimezone(TZ).date())
            or packet['timer']!=TIMER or packet['invocation']!=folder.name or not re.fullmatch('[a-f0-9]{32}',folder.name)
            or receipt['path']!=folder.relative_to(root).as_posix() or receipt['manifestSha256']!=sha(records/'manifest.json')
            or receipt['status']!=report['status']
            or not as_of<=instant(packet['computedAt'])<=instant(archive['created_at_utc'])
                <=instant(receipt['archiveVerifiedAt'])<=observed
            or set(archive['files'])!=set(hashes)
            or any(archive['files'][name]['sha256']!=digest for name,digest in hashes.items())):
        raise ValueError('Evaluation archive or receipt did not verify')
    return receipt,report


def archive_evaluation(root,store,report,invocation):
    day=instant(report['asOf']).astimezone(TZ).date()
    folder=root/LOG/str(day)/invocation
    records=folder/'records'
    records.mkdir(parents=True,exist_ok=False)
    bindings={name:sha(root/name) for name in CODE}
    create(records/'evaluation.json',dict(schemaVersion=1,report=report,invocation=invocation,timer=TIMER,
                                         computedAt=now().isoformat(),codeSha256=bindings))
    seal(records)
    archived=capture(root,store,[p.relative_to(root).as_posix() for p in records.iterdir()]+list(bindings))
    verify_archive(store,archived['snapshot'])
    create(folder/'receipt.json',dict(path=folder.relative_to(root).as_posix(),
                archiveSha256=archived['snapshot'],manifestSha256=sha(records/'manifest.json'),
                archiveVerifiedAt=now().isoformat(),status=report['status']))
    for p in (folder,folder.parent,folder.parent.parent):
        sync_dir(p)
    return verify_evaluation(root,store,folder)[0]


def run(root,store):
    from observation_out_of_sample import evaluate

    invocation=os.environ.get('INVOCATION_ID','')
    if os.environ.get('TRIGGER_UNIT')!=TIMER or not re.fullmatch('[a-f0-9]{32}',invocation):
        raise ValueError('Production evaluation requires its systemd timer')
    with lock(root/'.runtime/research-evaluation.lock'):
        return archive_evaluation(root,store,evaluate(root,store,now()),invocation)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--archive-store',type=Path,required=True)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--run',action='store_true')
    action.add_argument('--verify',type=Path)
    args=parser.parse_args()
    root,store=args.observation_root.resolve(),args.archive_store.resolve()
    result=verify_evaluation(root,store,args.verify)[0] if args.verify else run(root,store)
    print(json.dumps(result,ensure_ascii=False))
