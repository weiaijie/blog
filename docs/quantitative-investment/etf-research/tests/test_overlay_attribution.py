import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from interactive_backtest import DEFAULTS, CODES, backtest, inputs, same_window


class OverlayAttributionTests(unittest.TestCase):
    def test_endpoint_inventory_and_trade_cashflows_explain_components(self):
        params = dict(DEFAULTS,start='2025-10-29',end='2026-10-29',weights='1,1,1,3|3,1,0,6|1,0,0,1')
        report = same_window(params)
        info = report['attribution']
        base, _, bars, _ = inputs()
        for account in report['portfolios']:
            label = account['id']
            single = backtest(dict(params,weights=account['weights']))
            orders = single['orders']
            def quantity(fill):
                return fill['filled'] if fill['side']=='buy' else -fill['filled']
            def units(s, day):
                return sum(quantity(f) for f in orders if f['symbol']==s and f['day']<=day)
            for span in [info['holding'],*info['peakToTrough'].values()]:
                start, end = span['start'], span['end']
                part = span['accounts'][label]
                for s in CODES:
                    fills = [f for f in orders if f['symbol']==s and start<f['day']<=end]
                    price = (units(s,end)*bars[s][end].close-units(s,start)*bars[s][start].close
                             - sum(quantity(f)*f['open'] for f in fills))
                    dividends = sum(units(s,e.record_date)*e.per_share for e in base.dividends
                                    if e.symbol==s and start<e.ex_date<=end)
                    fee = -sum(f['fee'] for f in fills)
                    slip = sum(quantity(f)*(f['open']-f['modeled_price']) for f in fills)
                    self.assertEqual(part['byEtf'][s],dict(price=price,dividend=dividends,commission=fee,
                                                          slippage=slip,net=price+dividends+fee+slip))
                self.assertEqual(part['totals']['net'],part['endEquity']-part['startEquity'])
                for other in report['portfolios']:
                    if other['id']==label:
                        continue
                    key = label+'-'+other['id']
                    diff = span['differences'][key]
                    reference = span['accounts'][other['id']]
                    for s in CODES:
                        for k,v in diff['byEtf'][s].items():
                            self.assertEqual(v,part['byEtf'][s][k]-reference['byEtf'][s][k])
                    self.assertEqual(diff['totals']['net'],part['accountChange']-reference['accountChange'])
        self.assertEqual(info['holding']['differences']['B-A']['accountChange'],D('935.13'))
        self.assertEqual(info['peakToTrough']['A']['differences']['B-A']['accountChange'],D('2310.40'))

    def test_flat_accounts_have_zero_differences_and_no_peak_to_trough(self):
        params = dict(DEFAULTS,capital='1',weights='1,0,0,1|1,1,1,3',fees='high',rebalance='hold')
        details = same_window(params)['attribution']
        self.assertEqual(details['peakToTrough'],dict(A=None,B=None))
        self.assertTrue(all(v==0 for v in details['holding']['differences']['B-A']['totals'].values()))
