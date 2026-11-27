from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.evidence_archive import object_path
from etf_research.observation_slots import CALENDAR
from etf_research.publication import create, read, seal, sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import run_research_observation as obs
from seal_observation_decision import first_archive


class ResearchObservationTests(unittest.TestCase):
    def test_latest_session_and_bounded_repairs(self):
        days = tuple(date(2026,11,d) for d in (23,24,25,26,27))
        counts = Counter({days[0]:5,days[2]:1})
        self.assertEqual(obs.plan_days(days,counts,{days[1]},2),(days[4],days[3],days[2]))
        self.assertEqual(obs.plan_days(days,counts,{days[1],days[4]},2),(days[4],days[3],days[2]))
        self.assertEqual(obs.plan_days(days,counts,set(days),2),(days[4],))
        self.assertEqual(obs.plan_days((),counts,set(),2),())

    def test_timer_provenance(self):
        self.assertIsNone(obs.systemd_trigger({'TRIGGER_UNIT':'etf-research-daily.timer',
                                               'INVOCATION_ID':'a'*32}))
        self.assertIsNone(obs.systemd_trigger({'TRIGGER_UNIT':obs.TIMER,'INVOCATION_ID':'wrong'}))
        self.assertEqual(obs.systemd_trigger({'TRIGGER_UNIT':obs.TIMER,'INVOCATION_ID':'a'*32,
                                               'TRIGGER_TIMER_REALTIME_USEC':'123'})['timerRealtimeUsec'],123)

    def test_partial_never_qualifies(self):
        complete = dict(policy={'status':'archived'},
                        etf={code:{'status':'verified_estimate'} for code in obs.policy_etf.SYMBOLS},
                        market={'status':'full_capture'})
        self.assertTrue(obs.complete(complete))
        complete['etf']['511010']['status']='unknown'
        self.assertFalse(obs.complete(complete))

    def test_complete_archives_need_verified_timer_and_reproduce_origin(self):
        day = '2020-06-05'
        config = {'observationEarliestDate':day}
        slot = datetime.fromisoformat('2020-06-06T08:25:00+08:00')
        manager = dict(lastTriggerUsec=int(slot.timestamp()*1_000_000),calendar=sorted(CALENDAR))
        trigger = dict(unit=obs.TIMER,invocationId='a'*32,timerRealtimeUsec=0,
                       managerTimer=manager,managerTimerError=None,
                       managerTimerCheckedAt=(slot+timedelta(seconds=1)).isoformat())
        coverage = dict(policy={'status':'archived'},
                        etf={code:{'status':'verified_estimate'} for code in obs.policy_etf.SYMBOLS},
                        market={'status':'full_capture'})
        scheduled = dict(schemaVersion=1,date=day,phase='complete',coverage=coverage,trigger=trigger,
                         startedAt=(slot+timedelta(seconds=2)).isoformat(),
                         finishedAt=(slot+timedelta(minutes=2)).isoformat())
        missed = dict(scheduled,startedAt=(slot+timedelta(minutes=1)).isoformat())
        retry = dict(scheduled,trigger=dict(trigger,managerTimer=None,managerTimerError='ValueError'))
        manual = dict(scheduled,trigger=None)
        legacy_env = dict(scheduled,trigger=dict(unit=obs.TIMER,invocationId='a'*32,
                                               timerRealtimeUsec=manager['lastTriggerUsec']))
        incomplete = dict(scheduled,coverage=dict(coverage,market={'status':'partial_capture'}))
        for attempt in (missed,retry,manual,legacy_env,incomplete):
            self.assertFalse(obs.qualifies(attempt,config))
        self.assertTrue(obs.qualifies(scheduled,config))

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root, store = base/'root', base/'archive'
            log = root/'reports/research-observation'
            create(root/'config/research_observation.json',config)

            def files(folder):
                return [p.relative_to(root).as_posix() for p in folder.iterdir()]

            with patch.multiple(obs,ROOT=root,LOG=log,required_files=files):
                for name,result in (('missed',missed),('scheduled',scheduled)):
                    folder = log/'runs'/day/name
                    folder.mkdir(parents=True)
                    create(folder/'result.json',result)
                    (folder/'source.body').write_bytes(b'official source evidence')
                    seal(folder)
                    receipt = obs.archive_run(folder,store,config)
                    self.assertIs(receipt['forwardEligible'],name=='scheduled')
                    self.assertEqual(obs.check_receipt(folder,store,config),receipt)
                observed = datetime.now(timezone.utc)
                origin = first_archive(root,store,observed)
                self.assertEqual(origin['archiveSha256'],receipt['archive'])
                self.assertEqual(origin['archiveVerifiedAt'],receipt['archiveVerifiedAt'])
                self.assertIsNone(first_archive(root,store,slot))
                object_path(store,sha(folder/'source.body')).write_bytes(b'corrupt source')
                with self.assertRaisesRegex(ValueError,'Archive content mismatch'):
                    first_archive(root,store,observed)

    def test_interruption_is_archived_and_tampered_receipt_rejected(self):
        config = {'observationEarliestDate':'2026-11-27'}
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root, store = base/'root', base/'archive'
            log = root/'reports/research-observation'
            attempt = log/'runs/2026-11-27/example'
            attempt.mkdir(parents=True)
            create(attempt/'started.json',dict(schemaVersion=1,date='2026-11-27',
                 startedAt='2026-11-27T08:42:00+00:00',trigger=None))
            (attempt/'partial.body').write_bytes(b'raw response before interruption')
            def files(folder):
                return [p.relative_to(root).as_posix() for p in folder.iterdir()]
            with patch.multiple(obs,ROOT=root,LOG=log,required_files=files):
                receipts,issues = obs.ledger(store,config,repair=True)
                self.assertEqual(issues,[])
                self.assertEqual(receipts[0]['phase'],'interrupted')
                self.assertFalse(receipts[0]['forwardEligible'])
                raw = obs.receipt_path(attempt)
                proof = read(raw)
                proof['forwardEligible']=True
                raw.write_text(json.dumps(proof),encoding='utf-8')
                self.assertEqual(obs.ledger(store,config)[0],[])
