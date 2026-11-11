from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import adx_bond as audit
import factor_lab
from overlay_attribution import cumulative_ledger
from compare_three_markets import CODES,anniversary


class AdxBondTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((audit.REPORT/'comparison.json').read_text())

    def test_actual_intraday_exit_cash_and_record_entitlement(self):
        days=[date(2020,1,1)+timedelta(days=i) for i in range(4)]
        prices={'510300':[(100,100),(100,102),(98,95),(95,95)],
                '511010':[(80,80),(80,80),(80,80),(80,81)]}
        bars={s:{d:SimpleNamespace(open=D(o),close=D(c)) for d,(o,c) in zip(days,p)} for s,p in prices.items()}
        def rows(stock,bond,cash):
            return [dict(date=d,equity=D(cash[i])+stock[i]*bars['510300'][d].close+bond[i]*bars['511010'][d].close,
                         cash=D(cash[i]),available_cash=D(cash[i]),receivables=D(0),
                         **{'units_'+s:stock[i] if s=='510300' else bond[i] if s=='511010' else 0 for s in CODES})
                    for i,d in enumerate(days)]
        def order(i,s,side,n):
            return dict(day=days[i],symbol=s,side=side,filled=n,open=bars[s][days[i]].open,modeled_price=bars[s][days[i]].open,fee=D(0))
        adx=rows([0,100,0,0],[0,0,100,100],[10000,0,1800,1800])
        bond=rows([0,0,0,0],[0,100,100,100],[10000,2000,2000,2000])
        books={audit.ADX:(adx,[order(1,'510300','buy',100),order(2,'510300','sell',100),order(2,'511010','buy',100)]),
               'bonds':(bond,[order(1,'511010','buy',100)]),'balanced':(deepcopy(bond),[order(1,'511010','buy',100)])}
        prefixes={m:cumulative_ledger(*b,bars,[]) for m,b in books.items()}
        raw=audit.primitives(books,prefixes,bars,[])
        self.assertEqual([r['gap'] for r in raw],[D(200),D(-400),D(0)])
        self.assertEqual(raw[1]['components']['execution'],D(300))
        self.assertEqual(raw[2]['components']['capital'],D('-2.5'))
        self.assertEqual(raw[2]['components']['cash'],D('2.5'))
        result=audit.decomposition(raw)
        self.assertEqual(result['gap'],D(-200))
        self.assertEqual(result['components']['execution'],D(500))
        self.assertEqual(sum(result['components'].values()),D(-200))
        event=SimpleNamespace(symbol='510300',record_date=days[1],ex_date=days[3],per_share=D(1))
        adx[-1]['equity']+=100;adx[-1]['receivables']+=100
        prefixes={m:cumulative_ledger(*b,bars,[event]) for m,b in books.items()}
        raw=audit.primitives(books,prefixes,bars,[event])
        self.assertEqual(raw[-1]['components']['entitlement'],100)
        self.assertEqual(audit.decomposition(raw)['gap'],D(-100))

    def test_constant_exposure_has_zero_timing_and_favorable_switch_positive(self):
        empty=dict(execution=D(0),capital=D(0),cash=D(0),entitlement=D(0),commission=D(0),slippage=D(0))
        def row(stock,spread):
            return dict(equity=D(100),stockValue=D(stock),unitSpread=D(100)*D(spread),
                        heldSpread=D(stock)*D(spread),gap=D(stock)*D(spread),components=empty,risk={'stockDown':D(0)})
        constant=audit.decomposition([row(20,'.1'),row(20,'-.1')])
        self.assertEqual(constant['components']['timing'],0)
        selected=audit.decomposition([row(20,'.1'),row(0,'-.1')])
        self.assertEqual(selected['components']['allocation'],0)
        self.assertEqual(selected['components']['timing'],2)

    def test_2967_old_adx_endpoints_and_all_component_sums(self):
        old=json.loads((factor_lab.REPORT/'comparison.json').read_text())
        prior={(r['start'],r['years']):r for r in old['entries']}
        rows=self.report['windows']
        self.assertEqual(len(rows),len(prior))
        for r in rows:
            self.assertEqual(D(r['equities'][audit.ADX]),D(prior[r['start'],r['years']][audit.ADX]))
            self.assertEqual(D(r['gap']),D(r['equities'][audit.ADX])-D(r['equities']['bonds']))
            self.assertEqual(sum(D(x) for x in r['components'].values()),D(r['gap']))
            self.assertEqual(sum(D(x) for x in r['riskComponents'].values()),D(r['gapBalanced']))
        for years,stats in self.report['periods'].items():
            subset=[r for r in rows if r['years']==int(years)]
            self.assertEqual(stats['beatBonds'],sum(D(r['gap'])>0 for r in subset))
            self.assertEqual(stats['lagBonds'],sum(D(r['gap'])<0 for r in subset))
            self.assertEqual(stats['count'],stats['beatBonds']+stats['lagBonds']+stats['tieBonds'])

    def test_nonoverlap_each_chain_and_no_immature_tail_counted(self):
        from bisect import bisect_left
        base,_,_,_=audit.work.inputs()
        days=tuple(d for d in base.sessions if str(d)>=audit.DEFAULTS['start'])
        for years,chains in self.report['nonOverlapping'].items():
            self.assertEqual(len(chains),12)
            for chain in chains:
                for i,r in enumerate(chain['windows']):
                    start=date.fromisoformat(r['start']);end=date.fromisoformat(r['end'])
                    self.assertEqual(end,days[bisect_left(days,anniversary(start,int(years)))])
                    self.assertEqual(r['start'],chain['anchor'] if i==0 else chain['windows'][i-1]['end'])
                if chain['immatureTail']:
                    tail=chain['immatureTail']
                    self.assertLess(date.fromisoformat(tail['end']),anniversary(date.fromisoformat(tail['start']),int(years)))
                self.assertEqual(chain['summary']['count'],len(chain['windows']))

    def test_calendar_years_chain_continuous_accounts_and_compound(self):
        years=self.report['calendarYears']
        for model in audit.MODELS:
            growth=D(1)
            for i,y in enumerate(years):
                account=y['accounts'][model];growth*=1+D(account['totalReturn'])
                if i:self.assertEqual(account['startingEquity'],years[i-1]['accounts'][model]['endingEquity'])
            self.assertAlmostEqual(growth,1+D(self.report['fullPeriod']['accounts'][model]['totalReturn']),places=22)
        self.assertFalse(years[0]['complete']);self.assertFalse(years[-1]['complete'])
        self.assertTrue(all(y['complete'] for y in years[1:-1]))

    def test_selected_year_retains_positions_and_daily_rounding_reconciles(self):
        d=audit.detail(dict(audit.DEFAULTS,year='2022'))
        archived=next(y for y in self.report['calendarYears'] if y['year']==2022)
        self.assertEqual(d['mode'],'continuous_year')
        self.assertEqual(d['summary']['gap'],D(archived['gap']))
        self.assertNotEqual(d['summary']['accounts'][audit.ADX]['startingEquity'],D(audit.DEFAULTS['capital']))
        self.assertEqual(sum(r['gap'] for r in d['daily']),d['summary']['gap'])
        for key,total in d['summary']['components'].items():
            self.assertEqual(sum(r['components'][key] for r in d['daily']),total)
        for day in d['daily']:
            self.assertEqual(sum(day['components'].values()),day['gap'])
            for account in day['accounts'].values():
                for order in account['orders']:
                    self.assertEqual(order['signal'],day['executionDecision']['asOf'])

    def test_archive_corruption_and_invalid_year_fail_closed(self):
        audit._compare.cache_clear()
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'comparison.json').write_text('{}')
            with patch.object(audit,'REPORT',Path(folder)),self.assertRaisesRegex(ValueError,'checksum'):
                audit.compare(audit.DEFAULTS)
        audit._compare.cache_clear()
        for year in ('2027','2018','22','2022.0'):
            with self.subTest(year=year),self.assertRaises(audit.work.InputError):
                audit.detail(dict(audit.DEFAULTS,year=year))
