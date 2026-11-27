from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from observation_inputs import archive_for_day, assemble
from etf_research.observation_experiment import BASE, Window, availability
from etf_research.policy_events import instant
from etf_research.publication import read

PROOF = ROOT/'reports/2026-11-27-observation-inputs'
STORE = PROOF/'archive-proofs'


class ObservationInputTests(unittest.TestCase):
    def probe(self, name, store=STORE):
        file = PROOF/name
        saved = read(file)
        actual = assemble(ROOT,ROOT,store,date.fromisoformat(saved['entryDay']),
                          instant(saved['observedAt']),computed=instant(saved['computedAt']))
        return saved,actual

    def test_real_published_close_and_turnover_reconstruct_seven_inputs(self):
        saved,actual = self.probe('2026-11-30-probe.json')
        self.assertEqual(saved,actual)
        self.assertEqual(actual['anchorDay'],'2026-11-27')
        self.assertEqual(len(actual['lookbackSessions']),21)
        self.assertEqual({k for k,v in actual['cells'].items() if v is not None},set(BASE))
        self.assertAlmostEqual(actual['cells']['turnover20']['value'],1.2362978819615829)
        self.assertIsNone(actual['cells']['policyActiveCount'])
        self.assertEqual(actual['gaps']['policyActiveCount']['capturedCandidateCount'],10)
        self.assertFalse(actual['inputSealedForForecast'])
        self.assertGreater(instant(actual['computedAt']),instant(actual['observedAt']))
        self.assertEqual(actual['cells']['turnover20']['readyAt'],actual['computedAt'])
        window = Window(date(2026,11,27),(date(2026,11,30),*(date(2026,12,d) for d in range(1,5))))
        self.assertTrue(all(availability(actual['cells'][name],window) is not None for name in BASE))

    def test_late_handoff_stays_out_even_when_raw_numbers_exist(self):
        saved,actual = self.probe('2026-11-27-late-probe.json')
        self.assertEqual(saved,actual)
        self.assertEqual(actual['evidenceCutoff'],'2026-11-27T08:55:00+08:00')
        self.assertTrue(all(value is None for value in actual['cells'].values()))
        self.assertEqual(actual['gaps']['stockShareFlow'],'archive_not_ready')
        evening = instant('2026-11-27T17:41:00+08:00')
        row,error = archive_for_day(ROOT,STORE,date(2026,11,26),evening,
                                   read(ROOT/'config/research_observation.json'))
        self.assertIsNone(error)
        self.assertEqual(len(row['policyEtf']['etf']),2)
        self.assertTrue(all(f['relativeIntensity'] is not None for f in row['policyEtf']['etf']))
        self.assertIsNotNone(row['sse']['margin']['financingBuyShare'])

    def test_bad_archive_seal_leaves_affected_fields_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_store = Path(directory)
            (temp_store/'snapshots').mkdir()
            for manifest in (STORE/'snapshots').glob('*.json'):
                content = manifest.read_bytes()
                if manifest.name.startswith('edfe0c5'):
                    content += b'x'
                (temp_store/'snapshots'/manifest.name).write_bytes(content)
            _,actual = self.probe('2026-11-30-probe.json',temp_store)
        self.assertIsNotNone(actual['cells']['stockReturn5'])
        self.assertIsNone(actual['cells']['turnover20'])
        self.assertEqual(actual['gaps']['stockShareFlow'],'archive_proof_invalid')
        self.assertIsNone(actual['cells']['policyActiveCount'])
