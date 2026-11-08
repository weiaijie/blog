import sys
import unittest
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_three_markets import CODES, GROUPS, anniversary, metrics, simulate


class MarketComparisonTests(unittest.TestCase):
    def test_drawdown_last_equal_peak_and_recovery_at_exact_previous_high(self):
        days = [date(2025,1,1)+timedelta(days=i) for i in range(7)]
        result = metrics([dict(date=d,equity=D(v)) for d,v in zip(days,[100,110,110,88,99,110,105])])
        self.assertEqual((result['peak'],result['trough'],result['recovery']),(days[2],days[3],days[5]))
        self.assertEqual(result['trough_to_recovery_sessions'],2)
        self.assertEqual(result['peak_to_recovery_sessions'],3)
        self.assertLess(result['ending_drawdown'],0)

    def test_unrecovered_and_flat_paths(self):
        days = [date(2025,1,2),date(2025,1,3)]
        for values, recovery, observed in [([100,90],None,0),([100,100],days[0],None)]:
            r = metrics([dict(date=d,equity=D(v)) for d,v in zip(days,values)])
            self.assertEqual((r['recovery'],r['observed_since_trough_sessions']),(recovery,observed))
        self.assertEqual(anniversary(date(2024,2,29),1), date(2025,2,28))

    def test_equal_sleeve_uses_prior_close_and_skips_halted_open(self):
        days = [date(2025,1,2),date(2025,1,3),date(2025,1,6)]
        price = SimpleNamespace(open=D('1.000'),close=D('1.000'),low=D('1.000'),high=D('1.000'))
        bars = {s:dict.fromkeys(days,price) for s in CODES}
        rows, orders = simulate(days,bars,[],{(days[1],'513500')},GROUPS['equal'])
        self.assertEqual([r['target'] for r in orders],[16600,16600,16600,50000])
        self.assertEqual((orders[1]['filled'],orders[1]['reason']),(0,'opening_halt'))
        self.assertTrue(orders[0]['outside_range'])
        self.assertFalse(orders[1]['outside_range'])
        self.assertEqual(rows[0]['cash'],100000)
        self.assertEqual(rows[-1]['units_513500'],0)
