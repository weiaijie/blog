"""Seal completed monthly coverage from the independent production ledger."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from observation_labels import CALENDAR, EVIDENCE_ERRORS
from observation_monthly import LOG, month_report, parse_month
from observation_status import add_months
from etf_research.exchange_calendar import LOADER, calendar_at
from etf_research.evidence_archive import capture, safe_path, verify as verify_archive
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, lock, read, seal, sha, sync_dir, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
TIMER = 'etf-research-monthly-coverage.timer'
INVOCATION = re.compile(r'[a-f0-9]{32}')
CODE = (
    LOADER,
    'PROTOCOL_OBSERVATION_V1.md',CALENDAR,'config/research_observation.json',
    'deploy/etf-research-monthly-coverage.service','deploy/etf-research-monthly-coverage.timer',
    'scripts/observation_monthly.py','scripts/seal_observation_monthly.py',
    'scripts/observation_status.py','scripts/run_research_observation.py',
    'src/etf_research/admission.py','src/etf_research/evidence_archive.py',
    'src/etf_research/observation_decision_receipt.py','src/etf_research/publication.py',
)


def now():
    return datetime.now(timezone.utc)


def verify_month(root, store, folder, observed):
    folder = folder.resolve()
    records = folder/'records'
    verify_bundle(records)
    receipt = read(folder/'receipt.json')
    packet = read(records/'coverage.json')
    report = packet['report']
    archive = verify_archive(store,receipt['archiveSha256'])
    manifest_hash = sha(records/'manifest.json')
    bindings = {record.relative_to(root).as_posix():sha(record) for record in records.iterdir()}
    bindings.update(packet['inputSha256'])
    if (folder.parent.parent != root/LOG or folder.parent.name != report['month']
            or packet['timer'] != TIMER or packet['invocation'] != folder.name or not INVOCATION.fullmatch(folder.name)
            or receipt['path'] != folder.relative_to(root).as_posix() or receipt['manifestSha256'] != manifest_hash
            or report['state'] != 'ready_to_archive' or receipt['month'] != report['month']
            or not instant(report['sealAfter']) <= instant(report['asOf']) <= instant(packet['computedAt'])
                <= instant(archive['created_at_utc']) <= instant(receipt['archiveVerifiedAt']) <= observed
            or set(archive['files']) != set(bindings)
            or any(archive['files'][name]['sha256'] != digest for name,digest in bindings.items())):
        raise ValueError('Monthly coverage archive or receipt did not verify')
    return receipt,report


def find_month(root,store,month,observed):
    parse_month(month)
    states = dict(unverified=0,pending=0)
    verified = []
    for folder in sorted((root/LOG/month).glob('*')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        try:
            path = folder/'receipt.json'
            if not path.is_file():
                states['pending'] += 1
                continue
            if instant(read(path)['archiveVerifiedAt']) > observed:
                continue
            verified.append(verify_month(root,store,folder,observed))
        except EVIDENCE_ERRORS:
            states['unverified'] += 1
    return min(verified,key=lambda item:instant(item[0]['archiveVerifiedAt']),default=None),states


def month_view(root,store,month,observed):
    root,store = root.resolve(),store.resolve()
    sealed,issues = find_month(root,store,month,observed)
    receipt,report = sealed or (None,month_report(root,store,month,observed))
    state = 'verified' if receipt else 'unverified' if issues['unverified'] else 'waiting'
    return dict(schemaVersion=1,report=report,archive=dict(state=state,issues=issues,
                archiveSha256=receipt['archiveSha256'] if receipt else None,
                verifiedAt=receipt['archiveVerifiedAt'] if receipt else None))


def input_hashes(root,store,report):
    calendar = calendar_at(root,instant(report['asOf']))
    hashes = {name:sha(root/name) for name in (*CODE,*calendar.extensions)}
    log = 'reports/research-observation'
    for day in report['days']:
        for item in (*day['attempts'],*day['manualAttempts']):
            identity = item['archiveSha256']
            prefix = f"{log}/runs/{day['day']}/{item['id']}"
            receipt = f"{log}/archives/{day['day']}/{item['id']}.json"
            snapshot = verify_archive(store,identity)
            received = read(safe_path(root,receipt))
            if received['archive'] != identity or received['resultSha256'] != item['resultSha256']:
                raise ValueError('Monthly source receipt changed during build')
            hashes[receipt] = sha(safe_path(root,receipt))
            for leaf in ('started.json','result.json','manifest.json'):
                path = f'{prefix}/{leaf}'
                digest = sha(safe_path(root,path))
                if digest != snapshot['files'][path]['sha256']:
                    raise ValueError('Monthly source record differs from verified archive')
                hashes[path] = digest
        for issue in day['issues']:
            prefix = f"{log}/runs/{day['day']}/{issue['id']}"
            paths = [f'{prefix}/started.json']
            if issue['status'] == 'unverified':
                paths.extend([f'{prefix}/result.json',f'{prefix}/manifest.json',
                              f"{log}/archives/{day['day']}/{issue['id']}.json"])
            for name in paths:
                path = safe_path(root,name)
                if path.is_file():
                    hashes[name] = sha(path)
    return hashes


def archive_month(root,store,report,invocation):
    if report['state'] != 'ready_to_archive' or not INVOCATION.fullmatch(invocation):
        raise ValueError('Coverage month is not ready for scheduled seal')
    bindings = input_hashes(root,store,report)
    folder = root/LOG/report['month']/invocation
    records = folder/'records'
    records.mkdir(parents=True,exist_ok=False)
    create(records/'coverage.json',dict(schemaVersion=1,report=report,invocation=invocation,timer=TIMER,
                                       computedAt=now().isoformat(),inputSha256=bindings))
    seal(records)
    files = [path.relative_to(root).as_posix() for path in records.iterdir()]
    archived = capture(root,store,files+list(bindings))
    snapshot = verify_archive(store,archived['snapshot'])
    if any(snapshot['files'][path]['sha256'] != digest for path,digest in bindings.items()):
        raise ValueError('Input changed during monthly archive')
    create(folder/'receipt.json',dict(month=report['month'],path=folder.relative_to(root).as_posix(),
                archiveSha256=archived['snapshot'],manifestSha256=sha(records/'manifest.json'),
                archiveVerifiedAt=now().isoformat()))
    for path in (folder,folder.parent,folder.parent.parent):
        sync_dir(path)
    return verify_month(root,store,folder,now())[0]


def run(root,store):
    invocation = os.environ.get('INVOCATION_ID','')
    if os.environ.get('TRIGGER_UNIT') != TIMER or not INVOCATION.fullmatch(invocation):
        raise ValueError('Monthly production coverage requires its systemd timer')
    observed = now()
    current_month = observed.astimezone(TZ).date().replace(day=1)
    start = read(root/'config/research_observation.json')['observationEarliestDate'][:7]
    month = parse_month(start)
    sealed,waiting = [],[]
    with lock(root/'.runtime/research-monthly-coverage.lock'):
        while month < current_month:
            key = month.isoformat()[:7]
            existing,_ = find_month(root,store,key,observed)
            if existing is None:
                report = month_report(root,store,key,observed)
                if report['state'] == 'ready_to_archive':
                    sealed.append(archive_month(root,store,report,invocation))
                else:
                    waiting.append(dict(month=key,state=report['state']))
            month = add_months(month,1)
    return dict(observedAt=observed.isoformat(),sealed=sealed,waiting=waiting)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--archive-store',type=Path,required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--run',action='store_true')
    action.add_argument('--month')
    action.add_argument('--verify',type=Path)
    parser.add_argument('--as-of',help='Optional offset-aware clock for read-only coverage.')
    args = parser.parse_args()
    root,store = args.observation_root.resolve(),args.archive_store.resolve()
    if args.as_of and args.run:
        parser.error('--as-of is only available for read-only commands')
    observed = instant(args.as_of) if args.as_of else now()
    if args.month:
        output = month_view(root,store,args.month,observed)
    elif args.verify:
        output = verify_month(root,store,args.verify,observed)[0]
    else:
        output = run(root,store)
    print(json.dumps(output,ensure_ascii=False))
