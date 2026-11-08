import csv
from decimal import Decimal
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from interactive_backtest import DEFAULTS, InputError, backtest, request_params


class InteractiveBacktestTests(unittest.TestCase):
    def test_archived_fixed_windows_match_for_every_group_and_close(self):
        groups = {'510300':'1,0,0,1', '513500':'0,1,0,1', '159920':'0,0,1,1', 'equal':'1,1,1,3'}
        with (ROOT/'reports/2026-11-08-three-markets/daily.csv').open() as f:
            expected = list(csv.DictReader(f))
        for group, weights in groups.items():
            result = backtest(dict(DEFAULTS, weights=weights))
            balances = [(str(p['date']),p['equity']) for p in result['daily']]
            self.assertEqual(balances, [(p['date'],Decimal(p['equity'])) for p in expected
                                       if p['years']=='2' and p['group']==group])
            self.assertEqual(min(p['drawdown'] for p in result['daily']),result['summary']['max_drawdown'])

    def test_single_asset_custom_cash_fee_and_nontrading_endpoints(self):
        data = backtest(dict(DEFAULTS, start='2025-03-01', end='2025-03-30', weights='0,0,0,2.25',
                             rebalance='hold', capital='25900.25', fees='high'))
        orders = data['orders']
        self.assertEqual([r['symbol'] for r in orders], ['511010'])
        self.assertEqual(str(data['summary']['start']), '2025-03-03')
        self.assertEqual(str(data['summary']['end']), '2025-03-28')
        self.assertEqual(data['daily'][0]['equity'],Decimal('25900.25'))
        order = orders[0]
        self.assertGreater(order['filled'],0)
        self.assertEqual(order['fee'],max(Decimal(5), order['modeled_price']*order['filled']*Decimal('.001')).quantize(Decimal('.01')))
        flat = backtest(dict(DEFAULTS,capital='1',weights='0,0,0,1'))
        self.assertEqual(flat['summary']['max_drawdown'],0)
        self.assertEqual(flat['summary']['pnl'],0)

    def test_invalid_parameters(self):
        for change in [dict(weights='0,0,0,0'),dict(weights='1,-1,2,0'),dict(start='2024-02-30'),
                       dict(start='2018-01-01'),dict(fees='anything'),dict(capital='NaN'),
                       dict(start='2025-03-01',end='2025-03-02')]:
            with self.subTest(change=change), self.assertRaises(InputError):
                backtest(dict(DEFAULTS, **change))
        for query in ['start=a&start=b', 'start=a', 'arbitrary=true']:
            with self.assertRaises(InputError):
                request_params(query)
