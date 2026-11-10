import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from interactive_backtest import DEFAULTS, InputError, backtest, compare_windows, entry_windows, same_window


class SplitWindowTests(unittest.TestCase):
    def test_marked_sessions_and_rejections(self):
        params = dict(DEFAULTS,weights='0,1,0,1',start='2022-01-04',end='2022-03-28')
        self.assertEqual(backtest(params)['summary']['sessions'],55)
        self.assertEqual(entry_windows(params)['periods'][1]['count'],0)
        post = backtest(dict(params,start='2022-03-30',end='2022-12-30'))
        self.assertEqual(post['summary']['sessions'],186)
        for start,end in [('2022-03-28','2022-03-29'),('2022-03-29','2022-04-01'),('2022-03-25','2022-04-01')]:
            with self.subTest(start=start,end=end), self.assertRaisesRegex(InputError,'拆分停牌'):
                backtest(dict(params,start=start,end=end))
        with self.assertRaisesRegex(InputError,'组合 B'):
            compare_windows(dict(params,weights='0,0,1,1|0,0.01,1,1',end='2022-12-30'))

    def test_hong_kong_portfolios_keep_march_29_and_reconcile(self):
        params = dict(DEFAULTS,start='2022-01-04',end='2022-12-30',weights='0,0,1,1|1,0,0,1')
        result = same_window(params)
        for p in result['portfolios']:
            days = [str(r['date']) for r in p['daily']]
            self.assertEqual(len(days),242)
            self.assertIn('2022-03-29',days)
        pnl = result['attribution']['holding']['differences']['B-A']['accountChange']
        self.assertEqual(result['attribution']['dailyGaps']['B-A']['days'][-1]['cumulative'],pnl)
