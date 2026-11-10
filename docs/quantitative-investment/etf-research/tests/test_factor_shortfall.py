import json
import sys
import unittest
from decimal import Decimal as D
from datetime import date
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from factor_shortfall import exposure
from method_windows import archived_entries


class ShortfallTests(unittest.TestCase):
    def test_open_switch_overnight_and_dividend_entitlement(self):
        def ledger(stocks,bonds):
            return [dict(date=i,units_510300=s,units_511010=b) for i,(s,b) in enumerate(zip(stocks,bonds))]
        factor = ledger([0,100,0,100],[0,0,100,0])
        fixed = ledger([0,100,100,100],[0,0,0,0])
        bars = {s:{i:SimpleNamespace(open=o,close=c) for i,(o,c) in enumerate(p)}
                for s,p in [('510300',[(100,100),(100,100),(104,110),(113,114)]),
                            ('511010',[(50,50),(50,50),(50,52),(51,51)])]}
        event = SimpleNamespace(symbol='510300',record_date=2,ex_date=3,per_share=D(1))
        parts = exposure(factor,fixed,bars,[event])
        self.assertEqual((parts['exitStock'],parts['exitBond']),(-1000,100))
        self.assertEqual(parts['worstEpisode'],dict(signal=1,entry=2,exit=3,stock=-1000,bond=100,net=-900))

    def test_published_population_and_gap(self):
        report=json.loads((ROOT/'reports/2026-11-10-multifactor-shortfall/cohort.json').read_text())
        selected={}
        for (start,years),row in archived_entries().items():
            if years!=2:
                continue
            days=(date.fromisoformat(row['end'])-date.fromisoformat(start)).days
            nav=D(row['multifactor_v1'])
            if nav>100000 and (nav/D(100000))**(D('365.25')/days)<D('1.04'):
                selected[start]=row
        rows=report['windows']
        self.assertEqual(len(rows),len(selected))
        self.assertEqual({r['start'] for r in rows},selected.keys())
        for r in rows:
            entry=selected[r['start']]
            self.assertEqual(D(r['gap']),D(entry['multifactor_v1'])-D(entry['allocation']))
            self.assertEqual(D(r['gap']),sum(D(r[k]) for k in ('exitStock','exitBond','initialBonds','otherExposure'))-D(r['excessCost']))
            self.assertEqual(D(r['excessCost']),D(r['factorCommission'])+D(r['factorSlippage'])-D(r['allocationCommission'])-D(r['allocationSlippage']))
            threshold=D(r['threshold'])
            self.assertEqual(r['switchAddbackReached'],D(r['factorEquity'])+D(r['switchCommission'])+D(r['switchSlippage'])>=threshold)
            self.assertEqual(r['noCostReached'],D(r['noCostEquity'])>=threshold)
            self.assertEqual(r['retainReached'],D(r['retainEquity'])>=threshold)
        for key in ('missedRally','switchAddbackReached','noCostReached','retainReached'):
            self.assertEqual(report['counts'][key],sum(r[key] for r in rows))
        ordered=sorted(rows,key=lambda r:-abs(D(r['gap'])))
        self.assertEqual(report['largestAbsolute'],[r['start'] for r in ordered[:3]])
