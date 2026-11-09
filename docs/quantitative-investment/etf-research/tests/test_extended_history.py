import csv
import sys
import unittest
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from interactive_backtest import DEFAULTS, DOMESTIC_START, EXTENDED_START, InputError, backtest, comparison_inputs, configured_replay, inputs, same_window
from market_evidence import QUOTE_GAPS, START, evidence, verified_inputs


class ExtendedHistoryTests(unittest.TestCase):
    def test_domestic_matches_all_archived_daily_balances(self):
        p = dict(DEFAULTS,start=str(DOMESTIC_START),weights='1,0,0,1')
        days, _, replay = configured_replay(p)
        rows, _ = replay(days)
        with (ROOT/'reports/2026-11-05-long-history/monthly_50_50_base_100000_d1_daily.csv').open() as f:
            for row, expected in zip(rows,csv.DictReader(f),strict=True):
                self.assertEqual(str(row['date']),expected.pop('date'))
                self.assertEqual({k:row[k] for k in expected},{k:D(v) for k,v in expected.items()})
        self.assertEqual(len(rows),1967)
        # Domestic attribution must work across a gap in the unused S&P ETF data.
        gap = same_window(dict(p,start='2022-03-25',end='2022-04-06',weights='1,0,0,1|0,0,0,1'))
        self.assertEqual(gap['attribution']['holding']['accounts']['A']['byEtf']['513500']['net'],0)
        with self.assertRaises(InputError):
            comparison_inputs(dict(p,weights='1,0,0,1|1,0.01,0,1'))

    def test_extended_quotes_and_unchanged_legacy_window(self):
        domestic, dates, bars, halts = inputs()
        _, old_dates, old_bars, old_halts = verified_inputs(evidence())
        self.assertEqual((dates[0],len(dates)),(EXTENDED_START,925))
        self.assertEqual(tuple(d for d in dates if d>=START),old_dates)
        self.assertNotIn((date(2023,3,16),'513500'),halts)
        self.assertEqual(halts,old_halts)
        for code in QUOTE_GAPS:
            self.assertEqual(set(domestic.sessions)-bars[code].keys(),QUOTE_GAPS[code])
            self.assertTrue(all(bars[code][d]==old_bars[code][d] for d in old_dates))
        with self.assertRaises(InputError):
            backtest(dict(DEFAULTS,start='2022-12-30'))
