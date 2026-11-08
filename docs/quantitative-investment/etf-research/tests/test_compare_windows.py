import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from interactive_backtest import DEFAULTS, InputError, compare_windows, entry_windows


class CompareWindowsTests(unittest.TestCase):
    def test_three_portfolios_keep_shared_settings_and_separate_replays(self):
        shared = dict(DEFAULTS, start='2024-02-27', end='2026-03-03', capital='57219.18',
                      fees='high', rebalance='hold')
        vectors = ['3,1,0,6','1,0,0,1','0,1.25,4,2']
        result = compare_windows(dict(shared,weights='|'.join(vectors)))
        self.assertEqual([p['id'] for p in result['portfolios']],list('ABC'))
        for p, weights in zip(result['portfolios'],vectors,strict=True):
            reference = entry_windows(dict(shared,weights=weights))
            self.assertEqual(p, dict(id=p['id'], **reference))
            for stats in p['periods'].values():
                self.assertEqual(stats['worstReplay']['parameters']['weights'],weights)
                self.assertEqual(float(stats['worstReplay']['summary']['pnl']),stats['worstPnl'])

    def test_two_identical_portfolios_and_unmatured_horizon(self):
        params = dict(DEFAULTS, start='2024-02-28', end='2025-03-03', capital='1',weights='1,0,0,1|1,0,0,1')
        a,b = compare_windows(params)['portfolios']
        self.assertEqual(a['periods'],b['periods'])
        self.assertEqual(a['periods'][2]['count'],0)
        self.assertIsNone(b['periods'][2]['worstReplay'])
        self.assertEqual(a['periods'][1]['worstTies'],a['periods'][1]['count'])

    def test_invalid_vectors(self):
        for vectors in ['1,0,0,1','1,0,0,1|','1,0,0,1|0,0,0,0','|'.join(['1,1,1,3']*4)]:
            with self.subTest(vectors=vectors), self.assertRaises(InputError):
                compare_windows(dict(DEFAULTS,weights=vectors))
