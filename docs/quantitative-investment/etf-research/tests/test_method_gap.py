import csv
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from method_gap import ACCOUNTS, CASE, export_rows, gap_detail
from method_windows import archived_entries


class MethodGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = gap_detail(CASE)

    def test_daily_holdings_prices_and_cash_reconcile(self):
        previous = None
        for day in self.case['days']:
            for name in ACCOUNTS:
                account_change = 0
                for symbol, asset in day['assets'].items():
                    leg = asset[name]
                    before = previous['assets'][symbol][name]['after'] if previous else 0
                    self.assertEqual(leg['before'], before)
                    price_change = before * (asset['close'] - (asset['previousClose'] or asset['close']))
                    price_change += (leg['after'] - before) * (asset['close'] - asset['open'])
                    self.assertEqual(price_change, leg['price'])
                    self.assertEqual(leg['net'], sum(leg[k] for k in ('price','dividend','commission','slippage')))
                    account_change += leg['net']
                    for key, value in asset['difference'].items():
                        self.assertEqual(value, asset['installments'][key] - asset['allocation'][key])
                last_equity = previous['equity'][name] if previous else D(CASE['capital'])
                self.assertEqual(day['equity'][name] - last_equity, account_change)
            self.assertEqual(day['cumulative'], day['equity']['installments'] - day['equity']['allocation'])
            self.assertEqual(day['change'], sum(a['difference']['net'] for a in day['assets'].values()))
            previous = day

    def test_published_case_and_csv(self):
        r = self.case
        self.assertEqual(len(r['days']), 244)
        archived = archived_entries()[CASE['start'], 1]
        for name in ACCOUNTS:
            self.assertEqual(r['days'][-1]['equity'][name], D(archived[name]))
        self.assertEqual([r['byEtf'][s]['net'] for s in ('510300','511010')], [D('-68.13'),D('-753.13')])
        self.assertEqual(r['totals']['net'], D('-821.26'))
        self.assertEqual([str(d) for d in r['widening']], ['2021-11-02','2021-12-09','2021-12-08'])
        self.assertEqual([str(d) for d in r['worsening']], ['2021-11-11','2021-11-19','2021-11-04'])
        with (ROOT/'reports/2026-11-10-method-gap/daily.csv').open(encoding='utf-8',newline='') as file:
            expected = [{k:'' if v is None else str(v) for k,v in row.items()} for row in export_rows(r)]
            self.assertEqual(list(csv.DictReader(file)), expected)

    def test_flat_accounts(self):
        r = gap_detail(dict(CASE, capital='1', end='2021-11-05', installments='2', fees='high', rebalance='monthly'))
        self.assertEqual(r['totals']['net'], 0)
        self.assertEqual(r['widening'] + r['improving'] + r['worsening'], [])
