"""Observe independent research timers in the existing sealed health record."""
from datetime import datetime, time, timedelta, timezone
import re
import subprocess

from etf_research.policy_events import TZ, instant
from etf_research.publication import inside, read, verify_bundle

JOBS = ('calendar-watch','observation','model','decision','forecast','opening','label','evaluation',
        'monthly-coverage','observation-export')
FIELDS = ('Id','LoadState','ActiveState','UnitFileState','ActiveEnterTimestamp','TimersCalendar',
          'TimersMonotonic','Persistent','LastTriggerUSec','NextElapseUSecRealtime','Result',
          'ExecMainStartTimestamp','ExecMainExitTimestamp','ExecMainStatus')
TRIGGER_GRACE = timedelta(minutes=1)
STALE = timedelta(minutes=30)


def configuration(root, unit):
    timer_file = (root/'deploy'/(unit+'.timer')).read_text().splitlines()
    service_file = (root/'deploy'/(unit+'.service')).read_text().splitlines()
    calendar = sorted(line.partition('=')[2] for line in timer_file if line.startswith('OnCalendar='))
    slots = tuple(time.fromisoformat(re.fullmatch(r'\*-\*-\* (\d{2}:\d{2}:\d{2}) Asia/Shanghai',value)[1])
                  for value in calendar)
    if not slots:
        raise ValueError('Missing independent schedule')
    persistent, = [line.partition('=')[2]=='true' for line in timer_file if line.startswith('Persistent=')]
    setting, = [line.partition('=')[2] for line in service_file if line.startswith('TimeoutStartSec=')]
    timeout = re.fullmatch(r'(\d+)(min|s)',setting)
    return calendar,slots,persistent,timedelta(seconds=int(timeout[1])*(60 if timeout[2]=='min' else 1))


def parse_units(output):
    units={}
    for block in output.strip().split('\n\n'):
        properties={}
        calendar=[]
        for line in block.splitlines():
            name,_,value=line.partition('=')
            if name=='TimersCalendar':
                match=re.fullmatch(r'\{ OnCalendar=(.+?) ; next_elapse=.* \}',value)
                if match is None:
                    raise ValueError('Unrecognized systemd calendar')
                calendar.append(match[1])
            else:
                properties[name]=value
        properties['calendar']=sorted(calendar)
        if 'Id' in properties:
            units[properties['Id']]=properties
    return units


def read_units():
    units=[f'etf-research-{name}.{suffix}' for name in JOBS for suffix in ('timer','service')]
    arguments=['systemctl','--user','--timestamp=unix','show',*('--property='+name for name in FIELDS),*units]
    return parse_units(subprocess.check_output(arguments,text=True,timeout=8))


def stamp(value):
    if not value:
        return None
    if not re.fullmatch(r'@\d+',value):
        raise ValueError('Invalid systemd timestamp')
    return datetime.fromtimestamp(int(value[1:]),timezone.utc).astimezone(TZ)


def job_status(timer,service,spec,observed):
    calendar,slots,persistent,timeout=spec
    activated=stamp(timer.get('ActiveEnterTimestamp'))
    triggered=stamp(timer.get('LastTriggerUSec'))
    upcoming=stamp(timer.get('NextElapseUSecRealtime'))
    started=stamp(service.get('ExecMainStartTimestamp'))
    finished=stamp(service.get('ExecMainExitTimestamp'))
    dates=(observed.date()-timedelta(days=1),observed.date())
    ready=[datetime.combine(day,slot,TZ) for day in dates for slot in slots]
    due=max((slot for slot in ready if activated and activated<=slot<=observed),default=None)
    result=service.get('Result')
    exit_code=service.get('ExecMainStatus')
    if timer.get('LoadState')!='loaded' or service.get('LoadState')!='loaded':
        state='unit_unavailable'
    elif timer.get('ActiveState')!='active' or timer.get('UnitFileState')!='enabled':
        state='timer_inactive'
    elif (activated is None or timer.get('calendar')!=calendar or timer.get('TimersMonotonic')
            or timer.get('Persistent')!=('yes' if persistent else 'no')):
        state='timer_configuration_mismatch'
    elif service.get('ActiveState') in ('activating','active'):
        state='stalled' if started and observed-started>timeout else 'running'
    elif triggered is not None and not started and result not in (None,'success'):
        state='failed'
    elif started and triggered and triggered<=started<triggered+TRIGGER_GRACE and (
            result!='success' or exit_code!='0'):
        state='failed'
    elif due and observed>=due+TRIGGER_GRACE and (not triggered or triggered<due):
        state='missed_schedule'
    elif not upcoming:
        state='timer_configuration_mismatch'
    elif not due or not triggered or triggered<due:
        state='waiting'
    elif not started or not triggered<=started<triggered+TRIGGER_GRACE or not finished or finished<started:
        state='waiting' if observed<triggered+TRIGGER_GRACE else 'execution_unverified'
    else:
        state='late_trigger' if triggered>=due+TRIGGER_GRACE else 'completed'
    return dict(state=state,latestDueAt=due.isoformat() if due else None,
                lastTriggerAt=triggered.isoformat() if triggered else None,
                finishedAt=finished.isoformat() if finished else None,
                nextAt=upcoming.isoformat() if upcoming else None,result=result,exitStatus=exit_code)


def observe(root, observed, *, query=read_units):
    if observed.tzinfo is None:
        raise ValueError('Timezone-aware health time required')
    observed=observed.astimezone(TZ)
    try:
        units=query()
    except (OSError,ValueError,subprocess.SubprocessError):
        units={}
    jobs={}
    for name in JOBS:
        unit='etf-research-'+name
        try:
            jobs[name]=job_status(units[unit+'.timer'],units[unit+'.service'],configuration(root,unit),observed)
        except (OSError,ValueError,KeyError,TypeError):
            jobs[name]=dict(state='unit_unavailable',latestDueAt=None,lastTriggerAt=None,
                            finishedAt=None,nextAt=None,result=None,exitStatus=None)
    issues=[name for name,row in jobs.items() if row['state'] not in ('completed','waiting','running')]
    return dict(checkedAt=observed.isoformat(),state='attention' if issues else 'current',issues=issues,jobs=jobs)


def health_view(root, observed):
    path=root/'site/health_status.json'
    if not path.is_file():
        return dict(state='waiting',checkedAt=None,issues=[],jobs={})
    pointer=read(path)
    bundle=inside(root,pointer['observation'])
    verify_bundle(bundle)
    if read(bundle/'result.json')!=pointer:
        raise ValueError('Independent health snapshot differs from its seal')
    report=pointer.get('independent_study')
    if report is None:
        return dict(state='waiting',checkedAt=None,issues=[],jobs={})
    age=observed-instant(report['checkedAt'])
    if age < -TRIGGER_GRACE:
        raise ValueError('Independent health timestamp is ahead of the current time')
    return dict(report,state='stale' if age>STALE else report['state'])
