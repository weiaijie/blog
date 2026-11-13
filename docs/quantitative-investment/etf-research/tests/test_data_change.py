"""Maturity identity, exact metric bridge and controlled halt sensitivity."""
from datetime import date
from decimal import Decimal as D
from functools import partial
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import data_change_report as change
import interactive_backtest as work


class CohortTests(unittest.TestCase):
    def row(self,day,pnl):
        return change.measure(date(2024,1,day),date(2025,1,day),1,D('100000')+D(pnl))

    def test_halt_and_sample_effects_add_back_to_counts_and_worst(self):
        old=[self.row(1,-1000)];actual=old+[self.row(2,-2000)];relaxed=old+[self.row(2,5000)]
        result=change.compare_cohorts(old,actual,relaxed)
        self.assertEqual(result['addedMaturities'],1)
        self.assertEqual(result['sampleEffect']['profitable'],1)
        self.assertEqual(result['haltEffect']['profitable'],-1)
        self.assertEqual(result['haltEffect']['reached'],-1)
        self.assertEqual(result['haltEffect']['worstPnl'],D('-1000'))
        self.assertEqual(result['haltChangedWindows'],1)
        for k in result['delta']:
            self.assertEqual(result['delta'][k],result['sampleEffect'][k]+result['haltEffect'][k])

    def test_revised_old_endpoint_missing_and_duplicate_cohorts_rejected(self):
        old=[self.row(1,-1000)]
        for new in [[self.row(1,-999)],[self.row(2,-1000)],old+old]:
            with self.assertRaises(ValueError):change.compare_cohorts(old,new,new)

    def test_rate_can_fall_while_profitable_count_is_unchanged(self):
        old=[self.row(1,1000)];new=old+[self.row(2,-500)]
        result=change.compare_cohorts(old,new,new)
        self.assertEqual(result['delta']['profitable'],0)
        self.assertEqual(result['delta']['profitRate'],D('-.5'))

    def test_counterfactual_removes_only_new_sp500_halts(self):
        old=(date(2026,10,29),'513500');new=(date(2026,11,3),'513500');other=(date(2026,11,3),'159920')
        def fake(days,*,halts):return halts
        with patch.object(work,'configured_replay',return_value=((),D(100000),partial(fake,halts={old,new,other}))):
            self.assertEqual(change.cross_book(change.CONTROL,'2026-11-02','2026-11-12',True),{old,other})
            self.assertEqual(change.cross_book(change.CONTROL,'2026-11-02','2026-11-12'),{old,new,other})


class ArchivedChangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=change.report()

    def test_all_eleven_scenarios_have_nine_new_maturities_per_horizon(self):
        self.assertEqual(len(self.report['scenarios']),11)
        self.assertEqual(len(self.report['fullRecomputationChecks']),14)
        for scenario in self.report['scenarios']:
            for period in scenario['periods'].values():
                self.assertEqual(period['delta']['count'],9)
                self.assertEqual(len(period['newWindows']),9)
                self.assertTrue(all(w['end']>'2026-10-30' for w in period['newWindows']))
                self.assertEqual(period['haltChangedWindows'],0)
                self.assertEqual(D(period['delta']['worstPnl']),0)

    def test_positive_halt_control_has_reconciled_nonzero_effect_outside_mature_cohorts(self):
        detail=change.detail({'case':self.report['controlCase']})
        self.assertEqual(detail['case']['years'],0)
        self.assertTrue(any(o['reason']=='opening_halt' and o['filled']==0 for f in detail['actual']['frames'] for o in f['orders']))
        counter=detail['counterfactual']
        self.assertNotEqual(counter['effect'],D(0))
        self.assertEqual(sum(r['change'] for r in counter['dailyGap']['days']),counter['effect'])
        self.assertEqual(counter['contribution']['totals']['net'],counter['effect'])
        self.assertEqual(sum(p['net'] for p in counter['contribution']['byEtf'].values()),counter['effect'])
        self.assertTrue(any(t['symbol']=='513500' and t['filled']>0 for t in counter['orders']))

    def test_new_window_replay_matches_published_maturity_and_old_worst_uses_frozen_profile(self):
        s=self.report['scenarios'][0];p=s['periods']['2'];row=p['newWindows'][0]
        detail=change.detail({'case':row['case']})
        self.assertEqual(detail['actual']['frames'][-1]['pnl'],D(row['pnl']))
        self.assertEqual(self.report['cases'][p['before']['worstCase']]['dataVersion'],'frozen-2026-10-30')
        with self.assertRaises(work.InputError):change.detail({'case':'not-in-report'})


if __name__=='__main__':unittest.main()
