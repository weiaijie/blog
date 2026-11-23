"""Reconcile the sealed six-session change report and both sides of each halt diagnostic."""
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import november_change as change


class SixSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = change.report()

    def test_paired_counts_thresholds_and_worst(self):
        report = self.report
        self.assertEqual(len(report['scenarios']), 11)
        for scenario in report['scenarios']:
            for p in scenario['periods'].values():
                windows = p['newWindows']
                self.assertEqual(len(windows), 6)
                self.assertEqual(len({(w['start'], w['end']) for w in windows}), 6)
                self.assertTrue(all(w['end'] in report['newSessions'] for w in windows))
                self.assertEqual(sum(D(w['pnl']) > 0 for w in windows), p['delta']['profitable'])
                self.assertEqual(sum(D(w['annualized_return']) >= D('.04') for w in windows), p['delta']['reached'])
                self.assertEqual(min(D(p['before']['worstPnl']), *(D(w['pnl']) for w in windows)),
                                 D(p['after']['worstPnl']))
                self.assertEqual(sum(w['blockedOrders'] for w in windows), 0)
                self.assertEqual(p['haltChangedWindows'], 0)
                self.assertTrue(all(D(w['haltEffectPnl']) == 0 for w in windows))
                self.assertEqual(report['cases'][p['before']['worstCase']]['dataVersion'], change.RECENT)

    def test_all_six_controls_reconcile_and_do_not_count_as_maturities(self):
        r = self.report
        self.assertEqual(sorted(n['date'] for n in r['haltNotices']), r['openingHalts'])
        pairs = {(day, name) for day in r['openingHalts'] for name in ('market-equal','market-sp500')}
        self.assertEqual({(c['order']['day'], c['scenario']) for c in r['controls']}, pairs)
        for control in r['controls']:
            detail = change.detail({'case':control['case']})
            self.assertEqual(detail['case']['years'], 0)
            order = control['order']
            self.assertEqual((order['symbol'],order['side'],order['filled'],order['reason']),
                             ('513500','buy',0,'opening_halt'))
            self.assertTrue(any(o['symbol']=='513500' and o['filled']>0 for o in control['diagnosticOrders']))
            self.assertTrue(any(o['symbol']=='511010' and o['filled']>0 for o in control['actualOrders']))
            actual, other = detail['actual']['frames'], detail['counterfactual']
            self.assertEqual(actual[1]['equity']-other['curve'][1]['equity'], D(control['closeEffect']))
            self.assertEqual(other['effect'], D(control['endingEffect']))
            self.assertEqual(other['effect'], other['contribution']['totals']['net'])

    def test_new_worst_in_sp500_replays_to_published_equity(self):
        scenario = next(s for s in self.report['scenarios'] if s['id']=='market-sp500')
        p = scenario['periods']['2']
        detail = change.detail({'case':p['after']['worstCase']})
        self.assertEqual(detail['actual']['frames'][-1]['pnl'], D(p['after']['worstPnl']))
        self.assertEqual(D(p['delta']['worstPnl']), D('-50.64'))
