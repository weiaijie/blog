from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.publication import create, read

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import run_research_observation as obs


class ResearchObservationTests(unittest.TestCase):
    def test_latest_session_and_bounded_repairs(self):
        days = tuple(date(2026,11,d) for d in (23,24,25,26,27))
        counts = Counter({days[0]:5,days[2]:1})
        self.assertEqual(obs.plan_days(days,counts,{days[1]},2),(days[4],days[3],days[2]))
        self.assertEqual(obs.plan_days(days,counts,set(days),2),())

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
