import sys
import unittest
from pathlib import Path

from etf_research.policy_events import instant
from etf_research.publication import read

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from policy_source_watch import candidate, index_candidates
from research_day_coverage import cover, verify

SNAP = ROOT/'data/snapshots'
POLICY = (SNAP/'20261127T085055Z-13503987-policy-etf-day',
          SNAP/'20261127T085053Z-9ea3f925-policy-etf-day')
MARKET = (SNAP/'20261127T084226Z-10828286-sse-research-day',
          SNAP/'20261127T084227Z-669d6f01-sse-research-day')
REPORT = ROOT/'reports/2026-11-27-research-day-coverage'


class ResearchDayCoverageTests(unittest.TestCase):
    def test_late_data_is_unknown_instead_of_zero(self):
        day = cover(POLICY[1], MARKET[1], '2026-11-27T12:25:00+08:00')
        self.assertEqual(day['market']['status'], 'unknown_at_cutoff')
        self.assertIsNone(day['policy']['candidateCount'])
        self.assertEqual(day['etf']['510300']['status'], 'unknown_at_cutoff')
        self.assertFalse(day['forwardEligible'])

        intermediate = cover(POLICY[1], MARKET[1], '2026-11-27T16:45:00+08:00')
        self.assertEqual(intermediate['market']['status'], 'partial_capture')
        self.assertEqual(intermediate['policy']['status'], 'unknown_at_cutoff')

    def test_published_days_and_partial_capture(self):
        positive = verify(REPORT/'2026-11-26.json')
        partial = verify(REPORT/'2026-11-27.json')
        self.assertEqual(positive['etf']['510300']['estimatedNetSubscriptionCny'], '708184620.000000')
        self.assertEqual(positive['etf']['511010']['estimatedNetSubscriptionCny'], '46652430.00000')
        self.assertEqual(partial['market']['turnoverCny'], '930379000000.00')
        self.assertIsNone(partial['market']['margin'])
        self.assertIsNone(partial['etf']['511010']['featureReadyAt'])
        self.assertEqual(partial['policy']['signalEligibleCount'], 0)
        with self.assertRaisesRegex(ValueError, 'different exchange sessions'):
            cover(POLICY[0], MARKET[1], '2026-11-27T16:51:00+08:00')

    def test_official_revision_identity_and_stale_index(self):
        archived = read(POLICY[1]/'result.json')['policy']['candidates']
        gov = next(row for row in archived if row['index']=='gov_list')
        body = (POLICY[1]/gov['evidence']).read_bytes()
        fields = {k:gov[k] for k in ('index','url','title','indexDate')}
        receipt, checked = (instant(gov[k]) for k in ('receivedAt','candidateCheckedAt'))
        self.assertEqual(candidate(body,fields,receipt,checked)['revisionKey'], gov['revisionKey'])
        self.assertNotEqual(candidate(body+b' ',fields,receipt,checked)['revisionKey'], gov['revisionKey'])
        self.assertFalse(gov['signalEligible'])
        self.assertEqual(gov['published_at'], '2026-11-27T12:25:00+08:00')
        with self.assertRaisesRegex(ValueError, 'stale'):
            index_candidates('gov_list',(POLICY[1]/'gov_list.body').read_bytes(),
                             instant('2026-12-31T12:00:00+08:00').date())
