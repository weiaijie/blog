from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import method_windows as mw
import interactive_backtest as work


class MethodWindowsTests(unittest.TestCase):
    def test_all_six_worst_and_common_dates(self):
        summary=mw.compare(mw.DEFAULTS)
        raw=mw.archived_entries()
        seen={}
        for years,models in summary['periods'].items():
            for model,s in models.items():
                self.assertEqual(s['count'],1605 if years==1 else 1362)
                span=(s['worstStart'],s['worstEnd'])
                if span not in seen:
                    seen[span]=mw.detail(dict(mw.DEFAULTS,start=span[0],end=span[1]))['models']
                ledgers=seen[span]
                self.assertAlmostEqual(float(ledgers[model]['pnl']),s['worstPnl'],places=6)
                for m,ledger in ledgers.items():
                    self.assertEqual(ledger['pnl']+100000,D(raw[span[0],years][m]))
                    self.assertEqual([p['date'] for p in ledger['curve']],[p['date'] for p in ledgers[model]['curve']])
                    for day in ledger['events']:
                        self.assertEqual(day['day'],day['plan']['execution'])
                        self.assertLess(day['plan']['signal'],day['day'])
                        for order in day['orders']:
                            self.assertEqual(order['signal'],day['plan']['signal'])
                            self.assertEqual(order['target'],day['plan']['target'][order['symbol']])

    def test_custom_parameters_partial_maturities_and_ties(self):
        p=dict(mw.DEFAULTS,start='2024-02-28',end='2025-03-05',capital='57219.18',
               fees='high',rebalance='monthly',installments='2')
        s=mw.compare(p)['periods']
        for model,stats in s[1].items():
            self.assertGreater(stats['count'],1)
            check=mw.detail(dict(p,start=stats['worstStart'],end=stats['worstEnd']))['models'][model]
            self.assertAlmostEqual(float(check['pnl']),stats['worstPnl'],places=6)
            self.assertIsNone(s[2][model]['worstPnl'])
        tiny=mw.compare(dict(p,capital='1'))['periods'][1]
        for stats in tiny.values():
            self.assertEqual((stats['worstPnl'],stats['profitable'],stats['reached']),(0,0,0))
            self.assertEqual(stats['worstStart'],p['start'])
            self.assertEqual(stats['count'],stats['worstTies'])
        with self.assertRaises(work.InputError):
            mw.compare(dict(p,start='2018-09-14'))
