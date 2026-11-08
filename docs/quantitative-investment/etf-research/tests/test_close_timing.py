import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from attribute_close_timing import linked
from close_timing_sources import cash_close


class CloseTimingTests(unittest.TestCase):
    def test_missing_interior_with_equal_units_cancels(self):
        rows = [dict(previous='A',date='B',units=2),dict(previous='B',date='C',units=2)]
        self.assertEqual(linked(rows, {'A':Decimal(5),'C':Decimal(3)}), -4)

    def test_missing_rebalance_mark_blocks_total(self):
        rows = [dict(previous='A',date='B',units=2),dict(previous='B',date='C',units=3)]
        self.assertIsNone(linked(rows, {'A':Decimal(5),'C':Decimal(3)}))

    def test_us_close_dst_and_special_calendar(self):
        self.assertEqual(cash_close(date(2025,3,7)).utcoffset().total_seconds(), -5*3600)
        self.assertEqual(cash_close(date(2025,3,10)).utcoffset().total_seconds(), -4*3600)
        self.assertEqual(cash_close(date(2024,12,24)).hour, 13)
        self.assertIsNone(cash_close(date(2025,1,9)))
        self.assertIsNone(cash_close(date(2025,2,17)))
