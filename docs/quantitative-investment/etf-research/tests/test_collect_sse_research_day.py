from datetime import date, datetime
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from collect_sse_research_day import previous_session, verify


class CollectSseResearchDayTests(unittest.TestCase):
    def test_calendar_and_cutoff(self):
        friday = date(2026, 11, 27)
        with self.assertRaisesRegex(ValueError, 'not complete'):
            previous_session(friday, datetime.fromisoformat('2026-11-27T15:59:59+08:00'))
        self.assertEqual(previous_session(friday, datetime.fromisoformat('2026-11-27T08:00:00+00:00')),
                         date(2026, 11, 26))
        with self.assertRaisesRegex(ValueError, 'Not an exchange session'):
            previous_session(date(2026, 11, 28), datetime.fromisoformat('2026-11-28T17:00:00+08:00'))

    def test_complete_response_keeps_financing_residual(self):
        sample = verify(ROOT / 'data/snapshots/20261127T084226Z-10828286-sse-research-day')
        self.assertEqual(sample['status'], 'full_capture')
        self.assertEqual(sample['margin']['balanceIdentity']['residualCny'], '43')
        self.assertIsNone(sample['margin']['reconciledFinancingNetCny'])

    def test_missing_summary_preserves_turnover_and_unknown_margin(self):
        sample = verify(ROOT / 'data/snapshots/20261127T084227Z-669d6f01-sse-research-day')
        self.assertEqual(sample['status'], 'partial_capture')
        self.assertEqual(sample['turnoverCny'], '930379000000.00')
        self.assertIsNone(sample['margin'])
        self.assertIsNone(sample['publishedAt'])
        self.assertFalse(sample['historicalPointInTime'])
