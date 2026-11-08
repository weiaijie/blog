import json
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from interactive_backtest import DEFAULTS, backtest, entry_windows


class CustomWindowTests(unittest.TestCase):
    def test_presets_reproduce_archive_and_worst_drawdown(self):
        expected = json.loads((ROOT/'site/entry-windows.json').read_bytes())
        groups = {'equal':'1,1,1,3','510300':'1,0,0,1','513500':'0,1,0,1','159920':'0,0,1,1'}
        for group, weights in groups.items():
            report = entry_windows(dict(DEFAULTS, start=expected['firstSession'], weights=weights))
            for years, stats in report['periods'].items():
                with self.subTest(group=group,years=years):
                    archived = expected['periods'][str(years)]['groups'][group]
                    self.assertEqual({k:stats[k] for k in archived}, archived)
                    replay = stats['worstReplay']
                    self.assertEqual(replay['parameters']['weights'], weights)
                    curve = replay['daily']
                    self.assertEqual(str(curve[0]['date']),stats['worstStart'])
                    self.assertEqual(str(curve[-1]['date']),stats['worstEnd'])
                    self.assertEqual(float(curve[-1]['equity']-100000),stats['worstPnl'])
                    peak = D(100000)
                    for point in curve:
                        peak = max(peak,point['equity'])
                        self.assertEqual(point['drawdown'],point['equity']/peak-1)

    def test_custom_leap_and_weekend_windows_match_single_runs(self):
        params = dict(DEFAULTS, start='2024-02-28', end='2025-03-05', capital='75259.30',
                      weights='2.5,0,1,5', fees='high', rebalance='hold')
        endpoints = [('2024-02-28','2025-02-28'),('2024-02-29','2025-02-28'),
                     ('2024-03-01','2025-03-03'),('2024-03-04','2025-03-04'),('2024-03-05','2025-03-05')]
        runs = [backtest(dict(params,start=s,end=e)) for s,e in endpoints]
        stats = entry_windows(params)['periods']
        self.assertEqual(stats[1]['count'], len(runs))
        self.assertEqual(stats[1]['profitable'], sum(r['summary']['pnl']>0 for r in runs))
        self.assertEqual(stats[1]['reached'], sum(r['summary']['annualized_return']>=D('.04') for r in runs))
        self.assertEqual(stats[1]['worstReplay'], min(runs,key=lambda r:r['summary']['pnl']))
        self.assertEqual(stats[2],dict(count=0,profitable=0,reached=0,worstReplay=None))

    def test_flat_account_and_earliest_tie(self):
        params = dict(DEFAULTS, start='2024-02-28', end='2025-03-05', capital='1')
        stats = entry_windows(params)['periods'][1]
        self.assertEqual((stats['count'],stats['worstTies'],stats['profitable'],stats['reached']),(5,5,0,0))
        self.assertEqual(stats['worstStart'],params['start'])
        self.assertEqual(stats['worstReplay']['summary']['max_drawdown'],0)
