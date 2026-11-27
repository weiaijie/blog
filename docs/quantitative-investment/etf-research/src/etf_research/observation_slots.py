"""Bind research jobs to the actual recurring systemd timer activation."""
from datetime import datetime, time, timedelta, timezone
import re
import shlex
import subprocess

from .policy_events import TZ, instant

OBSERVATION_LOG = 'reports/research-observation'
ORIGIN_RECEIPT = OBSERVATION_LOG+'/origin.json'
TIMER = 'etf-research-observation.timer'


# Required policy polls remain stable. The added slot is an optional recovery.
POLL_TIMES = (time(8,25),time(19,40))
RETRY_TIME = time(8,34)
TIMER_TIMES = (POLL_TIMES[0],RETRY_TIME,POLL_TIMES[1])
CALENDAR = tuple(f'*-*-* {clock.isoformat()} Asia/Shanghai' for clock in TIMER_TIMES)
BUS = 'org.freedesktop.systemd1'
MANAGER = '/org/freedesktop/systemd1'
TIMER_INTERFACE = BUS+'.Timer'


def origin_source(receipt):
    match = re.fullmatch(OBSERVATION_LOG+r'/runs/(\d{4}-\d{2}-\d{2})/([a-zA-Z0-9-]+)', receipt['attempt'])
    if (match is None or receipt['session'] != match[1] or receipt['forwardEligible'] is not True
            or receipt.get('originReceiptSha256') is not None):
        raise ValueError('Invalid observation origin receipt')
    return f'{OBSERVATION_LOG}/archives/{match[1]}/{match[2]}.json'


def query(args):
    return shlex.split(subprocess.check_output(['busctl','--user',*args],text=True,timeout=3))


def manager_clock(unit, *, run_query=query):
    unit_reply = run_query(['call',BUS,MANAGER,BUS+'.Manager','GetUnit','s',unit])
    if len(unit_reply)!=2 or unit_reply[0]!='o' or not unit_reply[1].startswith(MANAGER+'/unit/'):
        raise ValueError('systemd did not resolve the timer unit')
    arguments = ['get-property',BUS,unit_reply[1],TIMER_INTERFACE]
    monotonic = run_query([*arguments,'TimersMonotonic'])
    calendar = run_query([*arguments,'TimersCalendar'])
    stamp = run_query([*arguments,'LastTriggerUSec'])
    if (monotonic!=['a(stt)','0'] or len(calendar)<2 or calendar[0]!='a(sst)'
            or not calendar[1].isdecimal() or len(calendar)!=2+3*int(calendar[1])
            or any(field!='OnCalendar' for field in calendar[2::3])
            or len(stamp)!=2 or stamp[0]!='t' or not stamp[1].isdecimal()):
        raise ValueError('systemd did not provide an exclusively calendar-based timer clock')
    return dict(lastTriggerUsec=int(stamp[1]),calendar=sorted(calendar[3::3]))


def with_manager_clock(trigger):
    try:
        evidence = manager_clock(trigger['unit'])
        error = None
    except (OSError,ValueError,subprocess.SubprocessError) as failure:
        evidence = None
        error = type(failure).__name__
    return dict(trigger,managerTimer=evidence,managerTimerCheckedAt=datetime.now(timezone.utc).isoformat(),
                managerTimerError=error)


def timer_identity(env, expected):
    unit, invocation = env.get('TRIGGER_UNIT'), env.get('INVOCATION_ID','')
    raw = env.get('TRIGGER_TIMER_REALTIME_USEC','')
    if unit!=expected or not re.fullmatch('[a-f0-9]{32}',invocation):
        return None
    value = int(raw) if re.fullmatch(r'\d{1,18}',raw) else None
    return dict(unit=unit,invocationId=invocation,timerRealtimeUsec=value)


def trigger_instant(microseconds):
    if type(microseconds) is not int or not 0<microseconds<4_102_444_800_000_000:
        return None
    return datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(microseconds=microseconds)


def manager_activation(trigger, unit, slots, started):
    if not trigger or trigger['unit']!=unit:
        return None
    evidence = trigger.get('managerTimer')
    expected = sorted(f'*-*-* {clock.isoformat()} Asia/Shanghai' for clock in slots)
    if (evidence is None or trigger.get('managerTimerError') is not None
            or evidence.get('calendar')!=expected
            or not re.fullmatch('[a-f0-9]{32}',trigger.get('invocationId',trigger.get('id','')))):
        return None
    checked = instant(trigger['managerTimerCheckedAt'])
    activated = trigger_instant(evidence.get('lastTriggerUsec'))
    return activated if activated is not None and activated<=checked<=started else None


def scheduled_slot(attempt):
    trigger = attempt['trigger']
    if not trigger or trigger['unit']!=TIMER:
        return None
    started = instant(attempt['startedAt'])
    if 'managerTimer' not in trigger:
        schedules = [(POLL_TIMES,trigger_instant(trigger.get('timerRealtimeUsec')))]
    else:
        schedules = [(slots,manager_activation(trigger,TIMER,slots,started)) for slots in (TIMER_TIMES,POLL_TIMES)]
    for slots,activated in schedules:
        if activated is None:
            continue
        local = activated.astimezone(TZ)
        planned = local.replace(second=0,microsecond=0)
        if planned.time() in slots and planned<=local<=started<planned+timedelta(minutes=1):
            return planned
    return None
