from datetime import date, datetime, timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.observation_experiment import BASE
from etf_research.policy_events import instant
from etf_research.publication import create, sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import seal_observation_decision as seal
from observation_status import report

DAY = date(2026,11,30)


class DecisionStatusTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)/'observations'
        self.store = Path(temporary.name)/'archive'
        calendar = self.root/seal.CALENDAR
        calendar.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/seal.CALENDAR,calendar)
        create(self.root/'config/research_observation.json',dict(observationEarliestDate='2026-11-27'))
        (self.root/'reports/research-observation').mkdir(parents=True)
        (self.store/'snapshots').mkdir(parents=True)

    def status(self, observed, day=None):
        return report(self.root,self.store,observed=instant(observed),day=day)

    def test_calendar_starts_on_first_enabled_trading_day(self):
        opened = self.status('2026-11-27T18:20:00+08:00')
        self.assertEqual(opened['decisionCounts']['expected'],0)
        self.assertEqual(opened['labelCounts'],dict(due=0,ready=0,gaps=0,holding=0,unknownCalendar=0))
        self.assertEqual(opened['nextDecision']['scheduledAt'],'2026-11-30T08:52:00+08:00')
        earlier = self.status('2026-11-27T18:20:00+08:00','2026-11-27')['session']
        self.assertEqual(earlier['decision']['status'],'prelaunch')
        closed = self.status('2026-11-28T11:00:00+08:00','2026-11-28')['session']
        self.assertEqual(closed['decision']['status'],'prelaunch')
        before = self.status('2026-11-30T08:54:59+08:00')
        self.assertEqual(before['sessions'][0]['status'],'awaiting_market_close')
        self.assertEqual(before['sessions'][0]['decision']['status'],'pending')
        self.assertEqual(before['decisionCounts']['expected'],0)
        after = self.status('2026-11-30T08:55:00+08:00')
        self.assertEqual(after['sessions'][0]['decision']['status'],'missing')
        self.assertEqual(after['decisionCounts'],dict(expected=1,sealedOnTime=0,eligibleInputDays=0,gaps=1))
        self.assertEqual(after['nextDecision']['scheduledAt'],'2026-12-01T08:52:00+08:00')

    def test_probes_and_incomplete_records_never_count(self):
        fixture = next((ROOT/seal.PROBES/str(DAY)).glob('*/receipt.json'))
        shutil.copytree(fixture.parent,self.root/seal.PROBES/str(DAY)/fixture.parent.name)
        now = '2026-11-30T09:00:00+08:00'
        self.assertEqual(self.status(now,str(DAY))['session']['decision']['status'],'missing')
        folder = self.root/seal.DECISIONS/str(DAY)/('1'*32)
        folder.mkdir(parents=True)
        self.assertEqual(self.status(now,str(DAY))['session']['decision']['status'],'incomplete')
        create(folder/'receipt.json',dict(archiveVerifiedAt='2026-11-30T08:54:00+08:00'))
        self.assertEqual(self.status(now,str(DAY))['session']['decision']['status'],'unverified')
        self.assertEqual(self.status(now)['decisionCounts']['sealedOnTime'],0)

    def test_actual_receipt_verification_drives_both_api_views(self):
        start = instant('2026-11-30T08:52:05+08:00')
        environment = dict(TRIGGER_UNIT=seal.TIMER, INVOCATION_ID='2'*32,
                           TRIGGER_TIMER_REALTIME_USEC=str(int((start-timedelta(days=1)).timestamp()*1_000_000)))
        actual = start-timedelta(seconds=2)
        source = dict(lastTriggerUsec=int(actual.timestamp()*1_000_000),calendar=['*-*-* 08:52:00 Asia/Shanghai'])
        available = dict(value=0,verified=True,asOf='2026-11-27',
                         receivedAt=start.isoformat(),readyAt=start.isoformat(),
                         dependencyReadyAt=[start.isoformat()],
                         evidence=[dict(root='prices',path=seal.CALENDAR,sha256=sha(self.root/seal.CALENDAR))])
        recovered = {'2026-11-27':{'turnover':dict(usedAttempt='original',retryAttempt='retry',
                                                   failedRequests=['market_20261127'],
                                                   dependencyReadyAt=[start.isoformat()])}}
        payload = dict(entryDay=str(DAY),anchorDay='2026-11-27',computedAt=start.isoformat(),
                       evidenceCutoff=start.isoformat(),cells={key:available if key in BASE else None for key in seal.FEATURES},
                       transportRecoveries=recovered,
                       gaps={'stockFinancingBuyShare':dict(reason='matched_margin_basis_missing')})
        origin = dict(date='2026-11-27',archiveVerifiedAt='2026-11-27T19:40:25+08:00')
        with (patch.object(seal,'CODE',(seal.CALENDAR,)), patch.object(seal,'now',return_value=start),
              patch.object(seal,'assemble',return_value=payload), patch.object(seal,'first_archive',return_value=origin),
              patch.object(seal,'with_manager_clock',side_effect=lambda trigger:dict(trigger,managerTimer=source,
                        managerTimerCheckedAt=start.isoformat(),managerTimerError=None)),
              patch('etf_research.evidence_archive.datetime') as archive_clock,
              patch.dict(seal.os.environ,environment,clear=True)):
            archive_clock.now.return_value = start
            result = seal.run(self.root,self.root,self.store)
        now = '2026-11-30T09:00:00+08:00'
        with patch.object(seal,'now',return_value=instant(now)):
            overview = self.status(now)
            summary = overview['sessions'][0]['decision']
            session = self.status(now,str(DAY))['session']
            detail = session['decision']
            self.assertEqual(session['label']['status'],'holding_period_incomplete')
            self.assertEqual(session['label']['notBefore'],'2026-12-04T16:00:00+08:00')
            self.assertEqual(overview['labelCounts']['holding'],1)
            self.assertEqual(overview['labelCounts']['due'],0)
            self.assertEqual(overview['decisionCounts'],dict(expected=1,sealedOnTime=1,eligibleInputDays=1,gaps=0))
            self.assertEqual(summary['latest'],detail['attempts'][0])
            self.assertEqual(summary['latest']['transportRecoveries'],recovered)
            self.assertEqual(summary['status'],'eligible_inputs')
            self.assertEqual(summary['latest']['featureGaps'],{'stockFinancingBuyShare':'matched_margin_basis_missing'})
            (self.root/result['decisionPath']/'records/inputs.json').write_bytes(b'{}')
            self.assertEqual(self.status(now,str(DAY))['session']['decision']['status'],'unverified')
            self.assertEqual(self.status(now)['decisionCounts']['eligibleInputDays'],0)
