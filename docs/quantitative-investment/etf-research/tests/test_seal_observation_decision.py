from datetime import date, datetime, timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.policy_events import TZ, instant
from etf_research.publication import create, read, sha
from etf_research.evidence_archive import restore

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))

import seal_observation_decision as decision
from observation_inputs import FEATURES
from etf_research.observation_experiment import BASE, VARIANTS

DAY = date(2026,11,30)


class ObservationDecisionTests(unittest.TestCase):
    def test_only_real_timed_schedule_and_archive_can_qualify(self):
        start = datetime(2026,11,30,8,52,tzinfo=TZ)
        cutoff = decision.deadline(DAY)
        source = decision.trigger_from(dict(TRIGGER_UNIT=decision.TIMER,INVOCATION_ID='a'*32,
                                      TRIGGER_TIMER_REALTIME_USEC=str(int(start.timestamp()*1_000_000))))
        record = dict(mode='scheduled',entryDay=str(DAY),startedAt=start.isoformat(),
                      finishedAt=(cutoff-timedelta(seconds=1)).isoformat(),trigger=source,
                      failure=None,studyOrigin=dict(date='2026-11-27', archiveVerifiedAt='2026-11-27T19:40:40+08:00'),
                      availableVariants=dict.fromkeys(VARIANTS,True))
        self.assertEqual(decision.decision_status(record,cutoff),'eligible_inputs')
        self.assertEqual(decision.decision_status(record,cutoff+timedelta(microseconds=1)),'missed_deadline')
        self.assertEqual(decision.decision_status(dict(record,trigger=None),cutoff),'missed_deadline')
        self.assertEqual(decision.decision_status(dict(record,mode='probe'),cutoff),'validation_only')
        self.assertEqual(decision.decision_status(dict(record,studyOrigin=None),cutoff),'study_origin_pending')
        future_origin = dict(date=str(DAY),archiveVerifiedAt=cutoff.isoformat())
        self.assertEqual(decision.decision_status(dict(record,studyOrigin=future_origin),cutoff),'study_origin_pending')
        self.assertEqual(decision.decision_status(dict(record,availableVariants={'baseline':False}),cutoff),
                         'missing_inputs')

    def test_manual_probe_archives_restores_and_retains_source_clocks(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            root, store = prefix/'obs', prefix/'store'
            calendar = root/decision.CALENDAR
            calendar.parent.mkdir(parents=True)
            shutil.copyfile(ROOT/decision.CALENDAR,calendar)
            create(root/'config/research_observation.json', {'observationEarliestDate':'2026-11-27'})
            now = decision.now()
            cutoff = min(instant('2026-11-30T08:55:00+08:00'),now)
            valid = dict(value=0,verified=True,asOf='2026-11-27',
                         receivedAt=(cutoff-timedelta(minutes=5)).isoformat(),
                         readyAt=now.isoformat(),dependencyReadyAt=[cutoff.isoformat()],
                         evidence=[dict(root='prices',path=decision.CALENDAR,sha256=sha(calendar))])
            fields = {k:valid if k in BASE else None for k in FEATURES}
            fields['stockFinancingBuyShare'] = dict(valid,value='0.06385012')
            inputs = dict(entryDay=str(DAY),anchorDay='2026-11-27',computedAt=now.isoformat(),
                          evidenceCutoff=cutoff.isoformat(),cells=fields)
            with patch.object(decision,'CODE',(decision.CALENDAR,)), patch.object(decision,'assemble',return_value=inputs):
                result = decision.run(root,root,store,probe=DAY)
            self.assertEqual(result['status'],'validation_only')
            self.assertTrue(result['availableVariants']['baseline'])
            self.assertTrue(result['availableVariants']['margin'])
            self.assertFalse(result['availableVariants']['combined'])
            self.assertFalse(result['forecastProduced'])
            self.assertFalse((root/decision.DECISIONS).exists())

            restored = prefix/'restored'
            restore(store,result['archiveSha256'],restored)
            folder = root/result['decisionPath']
            restored_folder = restored/result['decisionPath']
            shutil.copyfile(folder/'receipt.json',restored_folder/'receipt.json')
            self.assertEqual(decision.verify_decision(restored,store,restored_folder),result)

            record = read(restored_folder/'records/decision.json')
            self.assertEqual(record['inputSha256'],sha(restored_folder/'records/inputs.json'))
            (restored_folder/'records/inputs.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'Bundle hash mismatch'):
                decision.verify_decision(restored,store,restored_folder)

    def test_manual_invocation_cannot_write_production_history(self):
        with patch.dict(decision.os.environ,{},clear=True), self.assertRaisesRegex(ValueError,'timer provenance'):
            decision.run(ROOT,ROOT,ROOT)
