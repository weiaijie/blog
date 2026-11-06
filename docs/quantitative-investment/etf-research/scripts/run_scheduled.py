"""Supervise one scheduled run and retain success, failure and interrupted logs."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,os,signal,subprocess,sys,uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from etf_research.publication import read,sha,create,atomic,lock,seal
from etf_research.http_capture import client_version,load_policy

def timestamp():return datetime.now(timezone.utc).isoformat()
def invoke(root,refresh,out,err):
    command=[sys.executable,str(root/'scripts/run_daily.py')]
    if refresh:command+=['--rebuild']
    return subprocess.run(command,cwd=root,stdout=out,stderr=err,timeout=780,env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')).returncode

def scheduler_state():
    values={}
    for name,command in [('timer_enabled',['systemctl','--user','is-enabled','etf-research-daily.timer']),('timer_active',['systemctl','--user','is-active','etf-research-daily.timer']),('linger',['loginctl','show-user',str(os.getuid()),'--property=Linger','--value'])]:
        try:values[name]=subprocess.run(command,capture_output=True,text=True,timeout=5).stdout.strip()
        except (OSError,subprocess.TimeoutExpired):values[name]='unknown'
    return values

def supervise(root=ROOT,refresh=False,*,runner=invoke):
    root=Path(root);status_path=root/'site/operation_status.json'
    # This lock also prevents two supervisors racing on the latest status file.
    with lock(root/'.runtime/scheduler.lock'):
        previous=read(status_path) if status_path.exists() else {}
        run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
        folder=root/'reports/operations'/run_id;folder.mkdir(parents=True,exist_ok=False)
        relative=str(folder.relative_to(root));started=timestamp()
        mode='validation_refresh' if refresh else 'scheduled'
        unfinished=[str(p.parent.relative_to(root)) for p in (root/'reports/operations').glob('*/started.json') if not (p.parent/'result.json').exists()]
        begin=dict(schema_version=1,started_at_utc=started,mode=mode,operation=relative,unfinished_prior_operations=unfinished)
        create(folder/'started.json',begin)
        atomic(status_path,{**begin,'phase':'running','last_success':previous.get('last_success')})
        exit_code=1;result=None;error=None;before=None;after=None;transport=None
        try:
            before=read(root/'config/active_run.json');load_policy(root/'config/collection.json');transport=client_version()
            with (folder/'stdout.log').open('xb') as out,(folder/'stderr.log').open('xb') as err:
                exit_code=runner(root,refresh,out,err)
            if exit_code!=0:
                try:
                    candidate=json.loads((folder/'stdout.log').read_text(encoding='utf-8').splitlines()[-1])
                    if isinstance(candidate,dict) and candidate.get('status')=='blocked':result=candidate
                except (ValueError,IndexError):pass
            if exit_code==0:
                lines=(folder/'stdout.log').read_text(encoding='utf-8').splitlines()
                result=json.loads(lines[-1]) if lines else None
                if not isinstance(result,dict) or result.get('status') not in ('published','up_to_date'):raise ValueError('Child success lacks a validated pipeline result')
        except (Exception,KeyboardInterrupt) as exc:
            exit_code=124 if isinstance(exc,(subprocess.TimeoutExpired,InterruptedError,KeyboardInterrupt)) else 1
            error=dict(type=type(exc).__name__,message=str(exc))
        try:after=read(root/'config/active_run.json')
        except Exception as exc:
            exit_code=1;error=dict(type=type(exc).__name__,message='Active pointer could not be read after run')
        finished=timestamp();ok=exit_code==0
        summary={**begin,'finished_at_utc':finished,'phase':'success' if ok else 'failed','exit_code':exit_code,'result':result,'error':error,
            'account_through':after.get('as_of') if after else None,
            'checkpoint_sha256':after.get('checkpoint_sha256') if after else None,
            'account_changed':None if not before or not after else before['checkpoint_sha256']!=after['checkpoint_sha256'],
            'transport_version':transport,'scheduler':scheduler_state(),
            'last_success':dict(finished_at_utc=finished,operation=relative,mode=mode) if ok else previous.get('last_success')}
        create(folder/'result.json',summary);seal(folder);atomic(status_path,summary)
        return summary

def terminated(signum,frame):raise InterruptedError('Supervisor received termination signal')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--refresh-current',action='store_true',help='Controlled live-source acceptance only; never used by the daily timer');a=p.parse_args()
    signal.signal(signal.SIGTERM,terminated)
    try:
        result=supervise(refresh=a.refresh_current);print(json.dumps(result,ensure_ascii=False));raise SystemExit(result['exit_code'])
    except BlockingIOError:print(json.dumps(dict(phase='busy',account_changed=False)));raise SystemExit(75)
