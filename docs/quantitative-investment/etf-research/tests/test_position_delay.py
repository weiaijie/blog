from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_position_delay import components


class PositionAttributionTests(unittest.TestCase):
    def test_offsetting_market_moves_and_partial_cash_fill(self):
        # Original 50% target: 500 shares at 10. Execution day: 400 shares at 11.
        parts = components(D('.5'),D(10000),D(10500),D(10490),D(10),D(11),500,400,
                           'cash_limited_partial_or_zero')
        self.assertEqual([parts[k] for k in ('lot','price_move','nav_move','cash_limit','cost_nav')],
                         [0,500,-250,-1100,5])
        self.assertEqual(sum(parts.values()),400*11-D('.5')*10490)

    def test_blocked_sale_leaves_overweight(self):
        for why,key in [('known_ex_dividend_day','ex_guard'),('conservative_9pct_buffer','move_guard')]:
            with self.subTest(why=why):
                result = components(D(0),10000,10000,10000,D(10),D(9),0,100,why)
                self.assertEqual(result[key],900)
                self.assertEqual(result['cash_limit'],0)

    def test_unexplained_difference_stops_publication(self):
        with self.assertRaises(ValueError):
            components(D(1),10000,10000,10000,D(10),D(10),1000,900,'filled')
