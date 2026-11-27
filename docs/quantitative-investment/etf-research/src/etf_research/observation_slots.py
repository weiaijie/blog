"""Bind policy source polls to the actual recurring systemd timer activation."""
from datetime import datetime, time, timedelta, timezone
import re
import shlex
import subprocess

from .policy_events import TZ, instant

TIMER = 'etf-research-observation.timer'
POLL_TIMES = (time(8,25),time(19,40))
CALENDAR = tuple(f'*-*-* {clock.isoformat()} Asia/Shanghai' for clock in POLL_TIMES)
BUS = 'org.freedesktop.systemd1'
MANAGER = '/org/freedesktop/systemd1'
TIMER_INTERFACE = BUS+'.Timer'


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


def scheduled_slot(attempt):
    trigger = attempt['trigger']
    if not trigger or trigger['unit']!=TIMER:
        return None
    started = instant(attempt['startedAt'])
    if 'managerTimer' in trigger:
        evidence = trigger['managerTimer']
        if (evidence is None or trigger.get('managerTimerError') is not None
                or evidence.get('calendar')!=sorted(CALENDAR)
                or not re.fullmatch('[a-f0-9]{32}',trigger.get('invocationId',''))):
            return None
        checked = instant(trigger['managerTimerCheckedAt'])
        if checked>started:
            return None
        stamp_value = evidence.get('lastTriggerUsec')
    else:
        stamp_value = trigger.get('timerRealtimeUsec')
        checked = started
    if type(stamp_value) is not int or not 0<stamp_value<4_102_444_800_000_000:
        return None
    stamp = datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(microseconds=stamp_value)
    local = stamp.astimezone(TZ)
    planned = local.replace(second=0,microsecond=0)
    if planned.time() in POLL_TIMES and planned<=local<=checked<=started<planned+timedelta(minutes=1):
        return planned
    return None
