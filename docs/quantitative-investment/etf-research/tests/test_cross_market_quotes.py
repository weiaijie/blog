import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cross_market_quotes import END, THROUGH, checked_extension


class QuoteAdmissionTests(unittest.TestCase):
    def test_missing_day_conflict_revised_anchor_and_intraday_tail(self):
        base = {END:1}
        days = (THROUGH,)
        matched = {END:1,THROUGH:2,date(2026,11,10):3}
        sources = {p:matched.copy() for p in ('official','sina','sohu')}
        self.assertEqual(checked_extension(sources,base,days),{THROUGH:2})
        for bad in ({END:1},{END:1,THROUGH:3},{END:0,THROUGH:2},{THROUGH:2}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                checked_extension(dict(sources,sina=bad),base,days)
