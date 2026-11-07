from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_historical_pnl import drawdown_span, fill_details, reconcile_day


def bar(opening, close, low, high):
    return SimpleNamespace(open=D(opening), close=D(close), low=D(low), high=D(high))


class HistoricalPnlTests(unittest.TestCase):
    def test_rotation_separates_gap_intraday_slippage_and_ex_date_income(self):
        bars = {"510300": bar("9", "11", "9", "11"), "511010": bar("100", "99", "98", "101")}
        sell = dict(symbol="510300", side="sell", units=100, signed_slippage=D("-1"),
                    commission=D(5), sell_tax=D(0))
        parts = reconcile_day({"510300": 200, "511010": 100}, {"510300": 100, "511010": 100},
                              {"510300": D(10), "511010": D(101)}, bars, [sell],
                              {"510300": D(20), "511010": D(0)})
        self.assertEqual(parts["price_510300"], 0)
        self.assertEqual(parts["price_511010"], -200)
        self.assertEqual(sum(parts.values()), -186)

    def test_equal_boundary_and_below_market_sell(self):
        quote = bar("10", "10", "9.99", "10.01")
        trade = dict(day="2026-11-06", signal_date="2026-11-05", symbol="510300", side="sell", units=100,
                     raw_price="10", fill_price="9.99", notional="999", commission="5", tax="0")
        self.assertEqual(fill_details(trade, quote)["direction"], "within")
        below = fill_details(dict(trade, fill_price="9.98", notional="998"), quote)
        self.assertEqual((below["direction"], below["excess_amount"], below["signed_slippage"]),
                         ("below", D(1), D(-2)))

    def test_drawdown_begins_at_prior_peak(self):
        self.assertEqual(drawdown_span([D(x) for x in [100, 120, 108, 90, 110]]), (1, 3, D(".25")))
        self.assertEqual(drawdown_span([D(100), D(100)]), (0, 0, D(0)))
