from datetime import date
from decimal import Decimal as D
from types import SimpleNamespace as NS
import json, unittest
from pathlib import Path
from etf_research.bond_issues import issue_exposures
from etf_research.monthly import compare, index_levels
CFG=json.loads((Path(__file__).resolve().parents[1]/'config/monthly_benchmark.json').read_text())


class MonthlyReportTests(unittest.TestCase):
    def test_month_reset_and_dividend(self):
        days=[date(2026,1,29),date(2026,1,30),date(2026,2,2)]
        bars={s:{d:NS(close=D(p)) for d,p in zip(days,prices)} for s,prices in
              [('510300',['10','20','38']),('511010',['10','10','10'])]}
        data=NS(sessions=days, bars=bars, dividends=[NS(symbol='510300',ex_date=days[-1],per_share=D('2'))])
        self.assertEqual(index_levels(data,days,CFG),[D('1'),D('1.5'),D('2.25')])
        with self.assertRaises(ValueError):
            index_levels(data,days[::2],CFG)

    def test_one_observation_is_not_zero_risk_or_return(self):
        row=compare([date(2026,11,5)],[D(1)],[D(1)],{'2026':[]},CFG)[0]
        self.assertFalse(row['complete'])
        self.assertIsNone(row['tracking_error_annualized'])
        self.assertIsNone(row['net_return'])

    def test_aliases_and_unknown_do_not_disappear(self):
        fund=dict(nav='100',listed_nav_fraction='.6',listed_positions=[
            dict(code=c,fair_value='20') for c in ['a','b','c']])
        rows=issue_exposures(fund,{'a':'issue1','b':'issue1'},D(50),D(100))
        self.assertEqual([r['issue'] for r in rows],['issue1',None])
        self.assertEqual([D(r['portfolio_fraction']) for r in rows],[D('.2'),D('.1')])
        fund['listed_positions'][0]['code']='b'
        with self.assertRaises(ValueError):
            issue_exposures(fund,{},D(50),D(100))
