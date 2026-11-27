from datetime import date, datetime, timedelta
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from etf_research.observation_slots import CALENDAR, TIMER
from observation_continuity import audit, session_row
from pack_observation_evidence import restore_ledger

FULL=('policy','510300','511010','market','margin')
DAY=date(2026,11,27)
NEXT=date(2026,11,30)
PACK=ROOT/'reports/2026-11-27-portable-observation/pack/archive'


def when(value):
    return datetime.fromisoformat(value+'+08:00')


def receipt(ready, fields, *, manual=False, slot=False):
    ready=when(ready)
    start=ready-timedelta(seconds=2)
    phase='complete' if fields==FULL else 'partial'
    trigger=None
    if not manual:
        trigger=dict(unit=TIMER,invocationId='a'*32)
    if slot:
        trigger.update(managerTimer=dict(calendar=sorted(CALENDAR),
                           lastTriggerUsec=int(start.timestamp()*1_000_000)),
                       managerTimerError=None,managerTimerCheckedAt=start.isoformat())
    entry=dict(attempt='test/attempt',phase=phase,trigger=trigger,archive='a'*64,
               archiveVerifiedAt=ready.isoformat(),resultSha256='b'*64,
               forwardEligible=not manual and phase=='complete')
    record=dict(startedAt=start.isoformat(),finishedAt=ready.isoformat(),trigger=trigger,errors={},
                coverage=dict(policy=dict(status='archived' if 'policy' in fields else 'coverage_incomplete',
                                          candidateCount=0,signalEligibleCount=0),
                              etf={code:dict(status='verified_estimate' if code in fields else 'unknown',
                                             featureReadyAt=ready.isoformat()) for code in ('510300','511010')},
                              market=dict(turnoverCny='100' if 'market' in fields else None,
                                          featureReadyAt=ready.isoformat(),
                                          margin=dict(balanceIdentity=dict(status='matched')) if 'margin' in fields else None)))
    return entry,record


class ObservationContinuityTests(unittest.TestCase):
    def test_real_launch_separates_archive_from_timer_clock(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger=Path(temporary)/'ledger'
            restore_ledger(PACK.parent,ledger)
            view=audit(ledger,PACK,when('2026-11-27T21:30:00'))
        self.assertEqual((view['trackedSessions'],view['completedWindows'],view['qualifiedOnTime']),(1,0,0))
        self.assertEqual((view['daysWithScheduledArchive'],view['daysWithVerifiedTimer']),(1,0))
        row=view['days'][0]
        self.assertEqual(row['scheduledAttempts'],9)
        self.assertEqual(row['cutoffAt'],'2026-11-30T08:55:00+08:00')
        self.assertEqual(row['qualification'],'awaiting_cutoff')
        self.assertEqual(row['slots'][0]['state'],'unconfirmed_clock')
        self.assertEqual(row['slots'][0]['unconfirmed'][0]['id'],'20261127T114000Z-18f4f01f')
        self.assertEqual(row['slots'][1]['state'],'upcoming')

    def test_weekend_timer_confirmed_and_first_full_data_late(self):
        initial=receipt('2026-11-27T19:40:11',('policy','market'))
        weekend=receipt('2026-11-28T08:25:05',('policy','510300','market'),slot=True)
        manual=receipt('2026-11-29T08:25:05',FULL,manual=True)
        late=receipt('2026-11-30T09:00:05',FULL)
        row=session_row(DAY,NEXT,[initial,weekend,manual,late],[],when('2026-11-30T09:01:00'))
        self.assertEqual(row['qualification'],'qualified_late')
        self.assertEqual(row['sources']['margin']['status'],'late')
        self.assertEqual(row['sources']['510300']['status'],'on_time')
        self.assertEqual(row['verifiedSlots'],1)
        self.assertEqual(row['manualAttempts'],1)
        self.assertEqual(len(row['slots']),6)
        self.assertEqual(row['slots'][1]['state'],'verified')

    def test_optional_retry_is_only_listed_when_an_archive_proves_it(self):
        early=receipt('2026-11-28T08:25:05',('policy','510300','market'),slot=True)
        retry=receipt('2026-11-28T08:34:05',FULL,slot=True)
        observed=when('2026-11-28T08:50:00')
        without=session_row(DAY,NEXT,[early],[],observed)
        self.assertFalse(any('08:34' in row['at'] for row in without['slots']))
        accepted=session_row(DAY,NEXT,[early,retry],[],observed)
        proof=next(row for row in accepted['slots'] if '08:34' in row['at'])
        self.assertEqual(proof['state'],'verified')
        self.assertEqual(accepted['qualification'],'on_time')

    def test_waiting_and_no_scheduled_archive_are_separate(self):
        pending=session_row(DAY,NEXT,[],[dict(id='pending',status='pending_archive')],when('2026-11-27T19:45:00'))
        self.assertEqual(pending['qualification'],'awaiting_cutoff')
        self.assertEqual(pending['slots'][0]['state'],'awaiting_archive')
        missing=session_row(DAY,NEXT,[],[],when('2026-11-30T08:55:00'))
        self.assertEqual(missing['qualification'],'no_scheduled_archive')
        self.assertTrue(missing['cutoffPassed'])

    def test_audit_stops_at_first_twenty_real_exchange_sessions(self):
        with patch('observation_continuity.archive_index',return_value=({},{})):
            report=audit(ROOT,PACK,when('2026-12-31T20:00:00'))
        self.assertEqual((report['trackedSessions'],report['completedWindows']),(20,20))
        self.assertFalse(report['collecting'])
        self.assertEqual(report['missedCutoffRuns'][0]['sessions'],20)
        self.assertIsNone(report['calendarUnknownYear'])
