"""Read sealed operations and independently replay a specified account transition."""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.admission import load_incremental
from etf_research.first_session_plan import check_execution
from etf_research.forward import advance
from etf_research.official_history import parse_dayk
from etf_research.publication import encoded, inside, read, sha, verify_bundle
from audit_official_close import audit as official_audit
from run_daily import reconcile
from hashlib import sha256

TZ = ZoneInfo('Asia/Shanghai')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_bundle(folder):
    started = read(folder/'started.json')
    if not (folder/'manifest.json').exists():
        status = 'blocked' if (folder/'failure.json').exists() else 'incomplete'
        return dict(status=status, target=started['through'], bundle=folder.name)
    verify_bundle(folder)
    ready = read(folder/'ready.json')
    pointer = ready['pointer']
    require(inside(ROOT, pointer['bundle']) == folder and
            inside(ROOT, pointer['checkpoint']) == folder/'forward_checkpoint.json', 'Bundle path mismatch')
    state = read(folder/'forward_checkpoint.json')
    previous_path = inside(ROOT, started['previous_checkpoint'])
    previous = read(previous_path)
    require(sha(previous_path) == ready['input_sha256'][started['previous_checkpoint']], 'Previous checkpoint changed')
    day = date.fromisoformat(started['through'])
    require(str(day) == state['as_of'] == pointer['as_of'] and
            state['checkpoint_sha256'] == pointer['checkpoint_sha256'], 'Target day or digest mismatch')
    snapshots = ROOT/'data/snapshots'
    admission = read(folder/'admission.json')
    prices = admission['snapshot']
    require(inside(snapshots, prices).parent == snapshots, 'Unexpected price snapshot')
    data, computed = load_incremental(snapshots, prices)
    require(computed == admission and data.sessions[-1] == day, 'Admission replay mismatch')
    official = read(folder/'official_close.json')
    matches = [m for m in snapshots.glob('*/manifest.json')
               if sha(m) == official['source_manifest_sha256']]
    require(len(matches) == 1, 'Missing or ambiguous official snapshot')
    for manifest in (snapshots/prices/'manifest.json', matches[0]):
        require(ready['input_sha256'][manifest.relative_to(ROOT).as_posix()] == sha(manifest), 'Sealed source mismatch')
    require(official_audit(matches[0].parent.name, prices, day) == official, 'Official quote mismatch')
    now = datetime.fromisoformat(started['created_at_shanghai'])
    require(advance(data, previous, now=now) == state, 'Frozen ledger replay mismatch')
    accounts = list(state['portfolios'].values())
    appended = [str(d) for d in data.sessions if previous['as_of'] < str(d) <= str(day)]
    for symbol in data.bars:
        rawfile = matches[0].parent/('sse_dayk_'+symbol+'.body')
        official_days = parse_dayk(rawfile.read_text(),symbol)
        require(all(date.fromisoformat(d) in official_days for d in appended),
                'Missing exchange bar for an appended session')
    require(state['forward_sessions']-previous['forward_sessions'] == len(appended), 'Session delta mismatch')
    require(reconcile(data, previous, state) == read(folder/'reconciliation.json'), 'Journal reconciliation mismatch')
    intent = read(ROOT/'reports/2026-11-06-intent/plan.json')
    require(check_execution(intent,state) == read(folder/'intent_check.json'), 'First intent mismatch')
    return dict(status='replayed_extension' if appended else 'same_day_rebuild',
                bundle=folder.name, target=str(day), old_through=previous['as_of'], sessions_appended=appended,
                accounts=len(accounts), prior_checkpoint=previous['checkpoint_sha256'],
                checkpoint=state['checkpoint_sha256'], offline=started['offline_replay'],
                prices=prices, official=matches[0].parent.name,
                prior_daily_rows=sum(len(p['daily']) for p in previous['portfolios'].values()),
                new_daily_rows=sum(len(p['daily']) for p in accounts),
                added_model_trades=sum(1 for p in accounts for t in p['journal']
                                       if t['kind']=='trade' and t['day'] in appended))


def check_operation(folder):
    verify_bundle(folder)
    row = read(folder/'result.json')
    require(inside(ROOT, row['operation'])==folder, 'Operation path mismatch')
    started = read(folder/'started.json')
    require(all(row.get(k)==v for k,v in started.items()), 'Inconsistent start record')
    if row['phase']=='failed':
        return dict(status='failed', operation=folder.name, exit_code=row['exit_code'], error=row['error'], result=row['result'])
    require(row['phase']=='success' and row['exit_code']==0, 'Unfinished operation')
    result = row['result']
    if result['status']=='up_to_date':
        require(row['account_changed'] is False and result['network_requests']==result['account_changes']==0
                and result['as_of']==row['account_through'], 'Inconsistent no-op')
        before, after = row.get('account_before'), row.get('account_after')
        if before is not None or after is not None:
            require(before and before==after and after['checkpoint_sha256']==row['checkpoint_sha256']
                    and after['as_of']==result['as_of'], 'No-op changed its publication pointer')
        report=dict(status='up_to_date', operation=folder.name, target=result['as_of'])
        if row.get('systemd_trigger'):
            report['systemd_trigger']=row['systemd_trigger']
        return report
    require(result['status']=='published', 'Unknown publication state')
    bundle = inside(ROOT, result['bundle'])
    report = check_bundle(bundle)
    require(report['target']==row['account_through']==result['as_of']
            and report['checkpoint']==row['checkpoint_sha256']
            and row['account_changed']==bool(report['sessions_appended']), 'Operation/ledger mismatch')
    start_time=datetime.fromisoformat(row['started_at_utc'])
    bundle_time=datetime.fromisoformat(read(bundle/'started.json')['created_at_shanghai'])
    require(start_time<=bundle_time<=datetime.fromisoformat(row['finished_at_utc']), 'Bundle outside operation')
    before, after = row.get('account_before'), row.get('account_after')
    trigger = row.get('systemd_trigger') or {}
    if before is not None or after is not None:
        ready = read(bundle/'ready.json')
        require(before and after and sha256(encoded(before)).hexdigest()==ready['previous_pointer_sha256']
                and before['checkpoint']==read(bundle/'started.json')['previous_checkpoint']
                and after==dict(ready['pointer'],bundle_manifest_sha256=sha(bundle/'manifest.json')),
                'Operation publication pointers differ')
    if (row['mode']=='scheduled' and report['sessions_appended'] and not report['offline']
        and before and after and trigger.get('daily_timer') is True and trigger.get('invocation_id')):
        # The normal live collector derives both snapshot names from the bundle id.
        require(report['prices']==bundle.name+'-prices' and report['official']==bundle.name+'-official',
                'Operation did not use its own captures')
        finished=datetime.fromisoformat(row['finished_at_utc'])
        for name in (report['prices'],report['official']):
            requests=read(ROOT/'data/snapshots'/name/'requests.json')
            require(requests and all(bundle_time<=datetime.fromisoformat(r['requested_at_utc'])<=finished
                    for r in requests), 'Capture timestamps outside the publication run')
        report['status']='timer_published_new_sessions'
    report.update(operation=folder.name, mode=row['mode'], systemd_trigger=trigger)
    return report


def scan_day(day):
    rows=[]
    for f in sorted((ROOT/'reports/operations').glob('*/started.json')):
        started=read(f)
        if datetime.fromisoformat(started['started_at_utc']).astimezone(TZ).date()!=day:
            continue
        if not (f.parent/'manifest.json').exists():
            rows.append(dict(status='incomplete',operation=f.parent.name))
        else:
            rows.append(check_operation(f.parent))
    accepted=any(r['status']=='timer_published_new_sessions' and r['target']==str(day)
                 and str(day) in r['sessions_appended'] for r in rows)
    return dict(day=str(day),timer_extension_verified=accepted,operations=rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--day',type=date.fromisoformat)
    group.add_argument('--bundle',type=Path)
    parser.add_argument('--require-timer',action='store_true')
    args=parser.parse_args()
    if args.require_timer and args.day is None:
        parser.error('--require-timer requires --day')
    result=scan_day(args.day) if args.day else check_bundle(inside(ROOT,args.bundle))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.require_timer and not result['timer_extension_verified']:
        raise SystemExit(2)
