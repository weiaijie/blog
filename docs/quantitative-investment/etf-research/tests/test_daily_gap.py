import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from interactive_backtest import DEFAULTS, CODES, backtest, same_window
from overlay_attribution import PARTS


class DailyGapTests(unittest.TestCase):
    def test_all_dates_directions_factors_and_ranks(self):
        vectors = ['1,1,1,3','3,1,0,6','1,0,0,1']
        params = dict(DEFAULTS, start='2025-10-29', end='2026-10-29', weights='|'.join(vectors))
        accounts = {label:backtest(dict(params, weights=v))['daily'] for label,v in zip('ABC',vectors)}
        result = same_window(params)['attribution']
        for key,gap in result['dailyGaps'].items():
            target, reference = key.split('-')
            rows = gap['days']
            prior = D(0)
            expected = result['holding']['differences'][key]
            for row,a,b in zip(rows, accounts[target], accounts[reference], strict=True):
                self.assertEqual(row['date'], a['date'])
                self.assertEqual(a['date'], b['date'])
                diff = a['equity'] - b['equity']
                self.assertEqual(row['change'], diff-prior)
                self.assertEqual(row['cumulative'], diff)
                self.assertEqual(row['targetChange']-row['referenceChange'], row['change'])
                self.assertEqual(sum(row['totals'][k] for k in PARTS), row['change'])
                self.assertEqual(sum(row['byEtf'][s]['net'] for s in CODES), row['change'])
                prior = diff
            for s in CODES:
                for k in PARTS:
                    self.assertEqual(sum(r['byEtf'][s][k] for r in rows), expected['byEtf'][s][k])
            for name,sign in [('increases',1),('decreases',-1)]:
                ranked = sorted((-sign*r['change'],r['date']) for r in rows if sign*r['change']>0)
                self.assertEqual(gap[name], [d for _,d in ranked[:3]])
        gap = result['dailyGaps']['B-A']
        self.assertEqual(gap['days'][-1]['cumulative'], D('935.13'))
        index = {str(r['date']):r for r in gap['days']}
        self.assertEqual(index['2026-06-25']['byEtf']['511010']['dividend'],D('81.44'))
        self.assertEqual(index['2026-03-02']['totals']['commission'],D('10'))
        self.assertEqual(index['2026-03-02']['totals']['slippage'],D('0.60'))

    def test_identical_weights_no_spurious_markers(self):
        result = same_window(dict(DEFAULTS, start='2026-10-21', weights='2,1,0,3|2,1,0,3'))
        for gap in result['attribution']['dailyGaps'].values():
            self.assertFalse(gap['increases'] or gap['decreases'])
            self.assertTrue(all(r['cumulative']==0 and r['change']==0 for r in gap['days']))
