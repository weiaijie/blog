"""Independent read-only account health, with optional immutable observation output."""
from pathlib import Path
from datetime import datetime
import argparse, json, subprocess, sys, uuid
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from etf_research.health import evaluate
from etf_research.admission import TZ
from etf_research.data import verify_manifest
from etf_research.forward import digest, engine_digest
from etf_research.publication import read, sha, inside, verify_bundle, lock, create, seal, atomic
from etf_research.notice_workflow import review_queue
from run_scheduled import scheduler_state


def inspect(root=ROOT, now=None, scheduler=None):
    now = now or datetime.now(TZ)
    try:
        calendar = root / 'data/snapshots/2026-11-04-calendar-08'
        verify_manifest(calendar)
        active = read(root / 'config/active_run.json')
        bundle = inside(root, active['bundle']); verify_bundle(bundle)
        state = read(inside(root, active['checkpoint']))
        if (sha(bundle / 'manifest.json') != active['bundle_manifest_sha256'] or
            digest({k:v for k,v in state.items() if k != 'checkpoint_sha256'}) != state['checkpoint_sha256'] or
            state['engine_sha256'] != engine_digest() or state['real_money'] is not False or
            (active['as_of'], active['checkpoint_sha256']) != (state['as_of'], state['checkpoint_sha256'])):
            raise ValueError('Account integrity failed')
        operation = read(root / 'site/operation_status.json') if (root / 'site/operation_status.json').exists() else None
        if operation:
            folder = inside(root, operation['operation'])
            if operation['phase'] == 'running':
                begin = read(folder / 'started.json')
                if any(operation.get(k) != v for k,v in begin.items()): raise ValueError('Running status mismatch')
            else:
                verify_bundle(folder)
                if read(folder / 'result.json') != operation: raise ValueError('Operation status mismatch')
        result = evaluate(now, read(calendar / 'calendar.json')['holiday_ranges'], active, operation,
                          scheduler if scheduler is not None else scheduler_state(), review_queue(root))
        archive_file=root/'.runtime/archive_status.json'
        receipt=read(archive_file) if archive_file.exists() else None
        result['last_archive']=receipt
        if scheduler is None:
            archive_state={}
            for unit,keys in [('etf-research-archive.timer',['ActiveState','UnitFileState']),('etf-research-archive.service',['Result'])]:
                command=['systemctl','--user','show',unit]+['--property='+k for k in keys]
                output=subprocess.run(command,capture_output=True,text=True,timeout=5,check=True).stdout
                archive_state.update(line.split('=',1) for line in output.splitlines() if '=' in line)
            result['archive_scheduler']=archive_state
            if archive_state.get('ActiveState')!='active' or archive_state.get('UnitFileState')!='enabled':result['issues'].append('archive_scheduler_inactive')
            if archive_state.get('Result') not in ('success',):result['issues'].append('archive_failed')
        if receipt:
            age=(now-datetime.fromisoformat(receipt['finished_at_utc'])).total_seconds()
            if age>26*3600 or age< -60: result['issues'].append('archive_stale')
        else: result['issues'].append('archive_not_observed')
        result['actionable']=bool(result['issues'])
        if result['issues']: result['state']=result['issues'][0]
        return result
    except Exception as exc:
        return dict(schema_version=1, checked_at=now.isoformat(), state='integrity_or_health_error',
                    actionable=True, issues=[type(exc).__name__ + ': ' + str(exc)], report_only=True)


def record(root=ROOT):
    with lock(root / '.runtime/health.lock'):
        result = inspect(root)
        folder = root / 'reports/health' / (datetime.now(TZ).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
        result['observation'] = folder.relative_to(root).as_posix()
        create(folder / 'result.json', result); seal(folder)
        atomic(root / 'site/health_status.json', result)
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--record', action='store_true'); args = parser.parse_args()
    result = record() if args.record else inspect()
    print(json.dumps(result, ensure_ascii=False))
    # An alert is a successful observation, not a reason for a restart storm.
    raise SystemExit(0 if args.record or not result['actionable'] else 2)
