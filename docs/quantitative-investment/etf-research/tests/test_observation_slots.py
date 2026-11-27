from datetime import timedelta
from pathlib import Path
import unittest
from unittest.mock import patch

from etf_research.observation_slots import CALENDAR, POLL_TIMES, TIMER, manager_clock, scheduled_slot, with_manager_clock
from etf_research.policy_events import instant

SLOT = instant('2026-11-27T19:40:00+08:00')


class ObservationSlotTests(unittest.TestCase):
    def test_live_timer_clock_overrides_stale_environment_without_relaxing_cutoff(self):
        invocation = dict(unit=TIMER,invocationId='a'*32,
                          timerRealtimeUsec=int((SLOT-timedelta(minutes=16)).timestamp()*1_000_000))
        started = (SLOT+timedelta(seconds=1)).isoformat()
        attempt = dict(trigger=invocation,startedAt=started)
        self.assertIsNone(scheduled_slot(attempt))
        evidence = dict(lastTriggerUsec=int(SLOT.timestamp()*1_000_000),calendar=sorted(CALENDAR))
        with patch('etf_research.observation_slots.manager_clock',return_value=evidence), \
             patch('etf_research.observation_slots.datetime') as clock:
            clock.now.return_value = SLOT+timedelta(milliseconds=500)
            trigger = with_manager_clock(invocation)
        self.assertEqual(scheduled_slot(dict(attempt,trigger=trigger)),SLOT)
        self.assertEqual(trigger['timerRealtimeUsec'],invocation['timerRealtimeUsec'])
        late = (SLOT+timedelta(minutes=1)).isoformat()
        self.assertIsNone(scheduled_slot(dict(attempt,trigger=trigger,startedAt=late)))
        wrong_clock = dict(trigger,managerTimerCheckedAt=late)
        self.assertIsNone(scheduled_slot(dict(attempt,trigger=wrong_clock)))
        wrong_timer = dict(trigger,managerTimer=dict(evidence,calendar=['another timer']))
        self.assertIsNone(scheduled_slot(dict(attempt,trigger=wrong_timer)))
        no_current_proof = dict(trigger,timerRealtimeUsec=evidence['lastTriggerUsec'],
                                 managerTimer=None,managerTimerError='ValueError')
        self.assertIsNone(scheduled_slot(dict(attempt,trigger=no_current_proof)))

    def test_manager_requires_pure_calendar_schedule_and_records_each_slot(self):
        properties = {
            'TimersMonotonic':['a(stt)','0'],
            'TimersCalendar':['a(sst)',str(len(CALENDAR)),
                              *(item for slot in reversed(CALENDAR) for item in ('OnCalendar',slot,'1'))],
            'LastTriggerUSec':['t','1795779600000000'],
        }

        def reply(args):
            if args[0]=='call':
                self.assertEqual(args[-1],TIMER)
                return ['o','/org/freedesktop/systemd1/unit/registered_timer']
            return properties[args[-1]]

        self.assertEqual(manager_clock(TIMER,run_query=reply),
                         dict(lastTriggerUsec=1795779600000000,calendar=sorted(CALENDAR)))
        properties['TimersMonotonic'] = ['a(stt)','1','OnActiveUSec','45000000','10']
        with self.assertRaisesRegex(ValueError,'exclusively calendar'):
            manager_clock(TIMER,run_query=reply)

    def test_optional_retry_requires_the_new_systemd_calendar_and_preserves_old_slots(self):
        old = sorted(f'*-*-* {clock.isoformat()} Asia/Shanghai' for clock in POLL_TIMES)

        def attempt(at, calendar):
            clock = instant(at)
            trigger = dict(unit=TIMER,invocationId='a'*32,
                           managerTimer=dict(calendar=calendar,lastTriggerUsec=int(clock.timestamp()*1_000_000)),
                           managerTimerError=None,managerTimerCheckedAt=clock.isoformat())
            return dict(startedAt=(clock+timedelta(seconds=1)).isoformat(),trigger=trigger)

        original='2026-11-27T08:25:00+08:00'
        self.assertEqual(scheduled_slot(attempt(original,old)),instant(original))
        retry='2026-11-28T08:34:00+08:00'
        self.assertIsNone(scheduled_slot(attempt(retry,old)))
        self.assertEqual(scheduled_slot(attempt(retry,sorted(CALENDAR))),instant(retry))
        late=attempt('2026-11-28T08:35:00+08:00',sorted(CALENDAR))
        self.assertIsNone(scheduled_slot(late))

    def test_released_timer_has_no_startup_relative_trigger(self):
        source = Path(__file__).resolve().parents[1]/'deploy'/TIMER
        settings = source.read_text().splitlines()
        self.assertEqual(sorted(row.removeprefix('OnCalendar=') for row in settings if row.startswith('OnCalendar=')),
                         sorted(CALENDAR))
        self.assertIn('Persistent=true',settings)
        self.assertFalse(any(row.startswith('OnActiveSec=') for row in settings))
