import csv
from datetime import date
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import method_windows as mw
import interactive_backtest as work


class MethodWindowsTests(unittest.TestCase):
    def test_all_eight_worst_and_common_dates(self):
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
                        if m == mw.FACTOR_MODEL:
                            decision = day['decision']
                            self.assertEqual(decision['asOf'],day['plan']['signal'])
                            self.assertEqual(sum(f['passed'] for f in decision['factors']), day['plan']['votes'])
                            if decision['transition'] == 'switch':
                                self.assertTrue(day['changedFactors'])
                                self.assertNotEqual(day['previousVotes'] >= 2, decision['votes'] >= 2)
                            else:
                                self.assertIsNone(day['previousVotes'])
                        self.assertEqual(day['day'],day['plan']['execution'])
                        self.assertLess(day['plan']['signal'],day['day'])
                        for order in day['orders']:
                            self.assertEqual(order['signal'],day['plan']['signal'])
                            self.assertEqual(order['target'],day['plan']['target'][order['symbol']])

    def test_published_windows_keep_prior_outcomes_and_all_threshold_counts(self):
        old = mw.ARCHIVE.parent.parent/'2026-11-10-method-windows/entries.csv'
        archive = mw.archived_entries()
        with old.open(encoding='utf-8') as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows),len(archive))
        for old_row in rows:
            row = archive[old_row['start'],int(old_row['years'])]
            self.assertEqual({key:row[key] for key in old_row}, old_row)
        periods = mw.compare(mw.DEFAULTS)['periods']
        principal = D(mw.DEFAULTS['capital'])
        for years, stats in periods.items():
            group = [r for (_,y),r in archive.items() if y == years]
            required = [principal * D('1.04')**(D((date.fromisoformat(r['end']) -
                        date.fromisoformat(r['start'])).days)/D('365.25')) for r in group]
            for model, outcome in stats.items():
                nav = [D(r[model]) for r in group]
                self.assertEqual(outcome['profitable'],sum(v>principal for v in nav))
                self.assertEqual(outcome['reached'],sum(v>=cutoff for v,cutoff in zip(nav,required)))
                self.assertEqual(D(str(outcome['worstPnl'])), min(nav)-principal)

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
