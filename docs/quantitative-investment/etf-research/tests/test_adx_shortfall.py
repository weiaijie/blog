from copy import deepcopy
from collections import Counter
from datetime import date,timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import adx_shortfall as short
from overlay_attribution import cumulative_ledger
from compare_three_markets import CODES


class AdxShortfallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=short.archived()

    def test_exact_parent_selection_and_all_account_bridges(self):
        parent=short.selected();self.assertEqual(len(parent),321)
        self.assertEqual({r['start'] for r in self.report['windows']},set(parent))
        for row in self.report['windows']:
            p=parent[row['start']]['scenarios']['base'];c={k:D(v) for k,v in row['components'].items()}
            self.assertEqual(D(row['netGap']),D(p['gap']))
            self.assertEqual(D(row['grossGap']),D(p['fixedFillGrossGap']))
            self.assertEqual(sum(c.values()),D(row['netGap']))
            self.assertEqual(sum(c[k] for k in ('losingStock','winningStock','bondPrice','bondDividend')),D(row['grossGap']))
            self.assertLess(D(row['grossGap']),0)
            churn=row['churn'];op=row['opportunity']
            self.assertEqual(D(churn['netImprovement']),D(churn['priceDividendPath'])+D(churn['costsSaved']))
            self.assertEqual(D(churn['alternativeGrossGap']),D(row['grossGap'])+D(churn['priceDividendPath']))
            self.assertEqual(sum(map(D,op['components'].values())),D(op['selectedDaysGap']))
            self.assertEqual(D(op['selectedDaysGap'])+D(op['otherDaysGap']),D(op['fullBalancedGap']))

    def test_worst_ranks_and_reused_events_not_independent_windows(self):
        rows=sorted(self.report['windows'],key=lambda r:(D(r['grossGap']),r['start']))
        self.assertEqual(self.report['worstStarts'],[r['start'] for r in rows[:5]])
        count=Counter((p['exit'],p['reentry']) for r in rows for p in r['churn']['gaps'])
        self.assertEqual(len(count),2)
        for event in self.report['shortGapEvents']:self.assertEqual(event['windowCount'],count[event['exit'],event['reentry']])
        self.assertEqual(self.report['counts']['shortGapWindows'],270)
        self.assertEqual(sum(self.report['entryYears'].values()),321)

    def test_cancel_only_declared_actual_short_gap_targets(self):
        days=tuple(date(2020,1,1)+timedelta(days=i) for i in range(11))
        decisions={d:dict(regime='balanced' if i==0 or i==6 else 'bonds') for i,d in enumerate(days)}
        original=deepcopy(decisions)
        episodes=[dict(entry=days[1],exit=days[2],exitDecision={}),dict(entry=days[7],exit=days[8],entryDecision={})]
        schedule,pairs=short.cancel_short_gaps(days,decisions,episodes)
        self.assertEqual(pairs[0]['gapSessions'],5)
        self.assertEqual(pairs[0]['removedTargets'],[days[2],days[7]])
        self.assertEqual(set(schedule),{days[1],days[8]})
        self.assertEqual(decisions,original)
        episodes[1]['entry']=days[8]
        unchanged,pairs=short.cancel_short_gaps(days,decisions,episodes)
        self.assertEqual(pairs,[])
        self.assertEqual(set(unchanged),{days[1],days[2],days[7],days[8]})

    def test_missed_opportunity_excludes_initial_flat_exit_and_reentry(self):
        days=tuple(date(2020,1,1)+timedelta(days=i) for i in range(7));prices=list(map(D,[10,11,12,13,15,14,15]))
        bars={s:{d:SimpleNamespace(open=prices[i],close=prices[i]) for i,d in enumerate(days)} for s in CODES}
        def rows(stocks,cash):
            return [dict(date=d,equity=D(cash[i])+stocks[i]*prices[i],cash=D(cash[i]),available_cash=D(cash[i]),receivables=D(0),
                         **{'units_'+s:stocks[i] if s=='510300' else 0 for s in CODES}) for i,d in enumerate(days)]
        def order(i,side):return dict(day=days[i],symbol='510300',side=side,filled=1,open=prices[i],modeled_price=prices[i],fee=D(0))
        a=(rows([0,0,1,0,0,0,1],[100,100,88,101,101,101,86]),[order(2,'buy'),order(3,'sell'),order(6,'buy')])
        b=(rows([0,1,1,1,1,1,1],[100,89,89,89,89,89,89]),[order(1,'buy')])
        books={short.audit.ADX:a,'balanced':b}
        ledgers={m:cumulative_ledger(*book,bars,[]) for m,book in books.items()}
        result=short.missed_opportunity(days,books,ledgers)
        self.assertEqual([r['date'] for r in result['marked']],[days[4],days[5]])
        self.assertEqual(result['components']['stockUp'],-2)
        self.assertEqual(result['components']['stockDown'],1)
        self.assertEqual(result['selectedDaysGap'],-1)

    def test_worst_detail_rounds_days_orders_and_alternative_reconcile(self):
        result=short.detail(dict(start='2021-02-10'))
        summary=result['summary'];rows=result['replay']['daily']['days']
        self.assertEqual(summary['grossGap'],D('-7100.8'))
        self.assertEqual(sum(r['grossChange'] for r in rows),summary['grossGap'])
        self.assertEqual(sum(r['change'] for r in rows),summary['netGap'])
        self.assertEqual(sum(r['gross'] for r in result['episodes']),summary['stockGross'])
        self.assertEqual(sum(r['change'] for r in result['counterfactual']['daily']['days']),summary['churn']['netImprovement'])
        self.assertEqual(result['counterfactual']['pairs'][0]['exit'],date(2022,7,18))
        for r in rows:
            for book in r['accounts'].values():
                for order in book['orders']:self.assertLess(order['signal'],order['day'])
        changed=[r for r in rows if r['changedFactors'] and r['accounts'][short.audit.ADX]['orders']]
        self.assertTrue(changed)
        self.assertIn('future re-entry',result['counterfactual']['warning'])

    def test_no_short_gap_preserves_original_exactly(self):
        result=short.detail(dict(start='2022-07-25'))
        self.assertEqual(result['counterfactual']['pairs'],[])
        self.assertEqual(result['summary']['churn']['netImprovement'],0)
        self.assertEqual(result['counterfactual']['curve'],result['replay']['curves'][short.audit.ADX])

    def test_invalid_queries_and_corrupt_archive_fail_closed(self):
        for params in [dict(start='2000-01-01'),dict(start='2021-02-10',fees='low'),{}]:
            with self.assertRaises(short.work.InputError):short.detail(params)
        with self.assertRaises(short.work.InputError):short.compare(dict(fees='low'))
        short.archived.cache_clear()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'cohort.json').write_text('{}')
            with patch.object(short,'REPORT',Path(tmp)):
                with self.assertRaisesRegex(ValueError,'checksum'):short.archived()
        short.archived.cache_clear()


if __name__=='__main__':unittest.main()
