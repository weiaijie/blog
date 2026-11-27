"""Run and archive an independent research session without loading any trading account."""
import argparse
from collections import Counter
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import signal
from uuid import uuid4

import collect_policy_etf_day as policy_etf
import collect_sse_research_day as sse
from research_day_coverage import cover
from etf_research.admission import completed_date, sessions_between
from etf_research.evidence_archive import capture, verify as verify_archive
from etf_research.exchange_calendar import calendar_at
from etf_research.observation_slots import TIMER, with_manager_clock
from etf_research.policy_events import instant
from etf_research.publication import create, inside, lock, read, seal, sha, verify_bundle

ROOT = policy_etf.ROOT
LOG = ROOT/'reports/research-observation'
CONFIG = ROOT/'config/research_observation.json'
HEX_ID = re.compile('[0-9a-f]{32}')
HASH = re.compile('[0-9a-f]{64}')
BASE = (CONFIG,ROOT/'config/collection.json',sse.CALENDAR)
SCRIPTS = ('run_research_observation','research_day_coverage','collect_sse_research_day',
           'collect_market_state_pilot','market_state_pilot','collect_policy_etf_day',
           'policy_source_watch','etf_share_flow')


def now():
    return datetime.now(timezone.utc)


def systemd_trigger(env):
    invocation = env.get('INVOCATION_ID','')
    triggered_at = env.get('TRIGGER_TIMER_REALTIME_USEC','')
    if env.get('TRIGGER_UNIT') != TIMER or not HEX_ID.fullmatch(invocation):
        return None
    return dict(unit=TIMER,invocationId=invocation,
                timerRealtimeUsec=int(triggered_at) if triggered_at.isdecimal() else None)


def plan_days(expected, counts, qualified, recovery_limit):
    if not expected:
        return ()
    # Each timer invocation also polls policy sources after the session qualifies.
    newest = expected[-1]
    pending = (day for day in expected[:-1] if day not in qualified)
    repairs = sorted(pending, key=lambda day: (counts[day], day))[:recovery_limit]
    return (newest,*repairs)


def complete(coverage):
    return (coverage['policy']['status']=='archived'
            and set(coverage['etf'])==set(policy_etf.SYMBOLS)
            and all(row['status']=='verified_estimate' for row in coverage['etf'].values())
            and coverage['market']['status']=='full_capture')


def attempt(day, trigger):
    started = now()
    key = started.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8]
    folder = LOG/'runs'/day.isoformat()/key
    folder.mkdir(parents=True,exist_ok=False)
    begin = dict(schemaVersion=1,date=day.isoformat(),startedAt=started.isoformat(),trigger=trigger)
    create(folder/'started.json',begin)
    errors = {}
    parts = {}
    for label, collect in (('policyEtf',policy_etf.collect),('sse',sse.collect)):
        try:
            parts[label],_ = collect(day,folder/'inputs')
        except Exception as error:
            errors[label] = dict(type=type(error).__name__,description=str(error)[:500])
            if isinstance(error, InterruptedError):
                break
    coverage = None
    if len(parts)==2:
        try:
            coverage = cover(parts['policyEtf'],parts['sse'],now().isoformat())
        except Exception as error:
            errors['coverage'] = dict(type=type(error).__name__,description=str(error)[:500])
    phase = 'failed' if coverage is None else 'complete' if complete(coverage) else 'partial'
    create(folder/'result.json',dict(**begin,finishedAt=now().isoformat(),
                                    phase=phase,errors=errors,coverage=coverage))
    seal(folder)
    return folder


def required_files(folder):
    from etf_share_flow import SNAP
    files = set(BASE)
    for config_path in (folder/'inputs').glob('*/run.json'):
        run = read(config_path)
        clock = instant(run['startedAt'])
        calendar = calendar_at(ROOT,clock,pinned=run['calendarSha256'])
        files.update(ROOT/name for name in calendar.extensions)
    files.update((ROOT/'src/etf_research').glob('*.py'))
    files.update(ROOT/'scripts'/(name+'.py') for name in SCRIPTS)
    files.update((ROOT/'deploy').glob('etf-research-observation.*'))
    files.update(p for p in SNAP.iterdir() if p.is_file())
    files.update(p for p in folder.rglob('*') if p.is_file())
    return sorted(p.relative_to(ROOT).as_posix() for p in files)


def archive_run(folder, store, config):
    verify_bundle(folder)
    result = read(folder/'result.json')
    relative = folder.relative_to(ROOT).as_posix()
    files = required_files(folder)
    archived = capture(ROOT,store,names=files)
    snapshot = verify_archive(store,archived['snapshot'])
    if set(snapshot['files'])!=set(files):
        raise ValueError('Archive file list mismatch')
    summary_hash = sha(folder/'result.json')
    if snapshot['files'][relative+'/result.json']['sha256']!=summary_hash:
        raise ValueError('Archive attempt digest mismatch')
    # Only scheduled acquisition during the registered window can start the clock.
    eligible = (result['phase']=='complete' and result['trigger'] is not None
                and result['date']>=config['observationEarliestDate'])
    receipt = dict(schemaVersion=1,session=result['date'],attempt=relative,phase=result['phase'],
                   resultSha256=summary_hash,attemptManifestSha256=sha(folder/'manifest.json'),
                   trigger=result['trigger'],archive=archived['snapshot'],
                   archiveCreatedAt=snapshot['created_at_utc'],archiveVerifiedAt=now().isoformat(),
                   files=archived['files'],forwardEligible=eligible)
    create(receipt_path(folder),receipt)
    return receipt


def receipt_path(folder):
    return LOG/'archives'/folder.parent.name/(folder.name+'.json')


def check_receipt(folder, store, config, *, root=None):
    root = ROOT if root is None else root
    path = root/'reports/research-observation/archives'/folder.parent.name/(folder.name+'.json')
    receipt = read(path)
    identity = receipt['archive']
    if not HASH.fullmatch(identity):
        raise ValueError('Invalid archive identity')
    manifest = store/'snapshots'/(identity+'.json')
    if sha(manifest)!=identity or sha(folder/'manifest.json')!=receipt['attemptManifestSha256']:
        raise ValueError('Archive manifest or attempt changed')
    result_name = (folder/'result.json').relative_to(root).as_posix()
    archived = read(manifest)
    if (receipt['attempt']!=folder.relative_to(root).as_posix()
            or receipt['session']!=folder.parent.name
            or archived['files'][result_name]['sha256']!=receipt['resultSha256']
            or archived['files'][result_name.replace('result.json','manifest.json')]['sha256']!=receipt['attemptManifestSha256']
            or receipt['archiveCreatedAt']!=archived['created_at_utc']
            or sha(folder/'result.json')!=receipt['resultSha256']):
        raise ValueError('Archive receipt does not match the sealed attempt')
    result = read(folder/'result.json')
    eligible = (result['phase']=='complete' and result['trigger'] is not None
                and result['date']>=config['observationEarliestDate'])
    if (not instant(result['finishedAt']) <= instant(receipt['archiveCreatedAt']) <= instant(receipt['archiveVerifiedAt'])
            or result['date']!=receipt['session'] or result['phase']!=receipt['phase']
            or result['trigger']!=receipt['trigger'] or receipt['forwardEligible'] is not eligible):
        raise ValueError('Archive result differs from its receipt')
    return receipt


def ledger(store, config, repair=False):
    receipts, issues = [], []
    for folder in sorted((LOG/'runs').glob('*/*')):
        try:
            if repair and not receipt_path(folder).exists():
                if not (folder/'manifest.json').exists():
                    if not (folder/'result.json').exists():
                        started = read(folder/'started.json')
                        create(folder/'result.json',dict(**started,finishedAt=now().isoformat(),
                               phase='interrupted',errors={'runner':'Recovered unfinished attempt'},coverage=None))
                    seal(folder)
                archive_run(folder,store,config)
            receipts.append(check_receipt(folder,store,config))
        except (OSError, ValueError, KeyError) as error:
            issues.append(dict(attempt=folder.relative_to(ROOT).as_posix(),error=str(error)[:500]))
    return receipts,issues


def schedule(start, end, observed=None):
    ranges = calendar_at(ROOT,observed if observed is not None else now()).ranges
    return sessions_between(ranges,start,end)


def progress(store, config):
    receipts,issues = ledger(store,config)
    qualified = [row for row in receipts if row['forwardEligible']]
    first = min(qualified,key=lambda row:instant(row['archiveVerifiedAt']),default=None)
    current = now()
    try:
        expected = schedule(date.fromisoformat(config['observationEarliestDate']),completed_date(current))
    except ValueError as error:
        expected = ()
        issues.append(dict(calendar=str(error)))
    latest = {}
    for row in sorted(receipts,key=lambda rec:instant(rec['archiveVerifiedAt'])):
        latest[row['session']] = row
    qualified_days = {row['session'] for row in qualified}
    return dict(schemaVersion=1,reportedAt=current.isoformat(),
                firstQualifiedArchive=first,qualifiedDays=sorted(qualified_days),
                expectedDays=[str(d) for d in expected],
                missingDays=[str(d) for d in expected if str(d) not in latest],
                latestAttempts=list(latest.values()),issues=issues)


def run(store, config, explicit_day):
    trigger = systemd_trigger(os.environ) if explicit_day is None else None
    if explicit_day is None and trigger is None:
        raise ValueError('Scheduled acquisition requires the independent systemd timer trigger')
    if trigger is not None:
        trigger = with_manager_clock(trigger)
    with lock(ROOT/'.runtime/research-observation.lock'):
        receipts,_ = ledger(store,config,repair=True)
        if explicit_day is not None:
            sse.previous_session(explicit_day,now())
            days = (explicit_day,)
        else:
            expected = schedule(date.fromisoformat(config['observationEarliestDate']),completed_date(now()))
            counts = Counter(date.fromisoformat(r['session']) for r in receipts if r['trigger'])
            qualified = {date.fromisoformat(r['session']) for r in receipts if r['forwardEligible']}
            days = plan_days(expected,counts,qualified,config['maxRecoveriesPerTrigger'])
        outcomes = [archive_run(attempt(day,trigger),store,config) for day in days]
        return dict(trigger=trigger,attempts=outcomes,progress=progress(store,config))


def interrupted(signum, frame):
    raise InterruptedError('Research runner interrupted')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',required=True,type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--day',type=date.fromisoformat,help='Manual evidence probe or late-data recovery')
    mode.add_argument('--status',action='store_true')
    args = parser.parse_args()
    settings = read(CONFIG)
    if (settings['schemaVersion']!=1 or type(settings['maxRecoveriesPerTrigger']) is not int
            or not 0<=settings['maxRecoveriesPerTrigger']<=4):
        parser.error('Unsupported observation configuration')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        result = progress(args.store,settings) if args.status else run(args.store,settings,args.day)
        print(json.dumps(result,ensure_ascii=False))
    except (OSError, ValueError) as error:
        print(json.dumps(dict(status='blocked',error=str(error)),ensure_ascii=False))
        raise SystemExit(1)
