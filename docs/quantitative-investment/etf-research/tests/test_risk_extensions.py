from datetime import date
from decimal import Decimal as D
from pathlib import Path
import json,unittest
import numpy as np
import pandas as pd
from etf_research.risk_extensions import beta_metrics,exposure_stress,benchmark_returns
from etf_research.accounting import Dividend
from etf_research.data import Dataset,RawBar

class RiskExtensionTests(unittest.TestCase):
    def test_known_beta(self):
        dates=pd.date_range('2024-01-01',periods=253);x=np.linspace(-.02,.02,252)
        nav=np.r_[100,100*np.cumprod(1+2*x)]
        r=beta_metrics(dates,nav,pd.Series(x,index=dates[1:]))
        self.assertAlmostEqual(r['beta'],2,places=12)
        self.assertAlmostEqual(r['correlation'],1,places=12)
    def test_forward_not_padded(self):
        dates=pd.date_range('2026-11-05',periods=2)
        r=beta_metrics(dates,[100,101],pd.Series([.02],index=dates[1:]))
        self.assertIsNone(r['beta']);self.assertEqual(r['window_returns'],1)
    def test_missing_benchmark_rejected(self):
        with self.assertRaisesRegex(ValueError,'missing'):beta_metrics(['2024-01-01','2024-01-02'],[100,101],pd.Series(dtype=float))
    def test_constant_benchmark_not_zero_beta(self):
        dates=pd.date_range('2024-01-01',periods=253)
        r=beta_metrics(dates,[100]*253,pd.Series([.01]*252,index=dates[1:]))
        self.assertIsNone(r['beta']);self.assertEqual(r['status'],'constant_benchmark')
    def test_cash_beta_zero_correlation_unknown(self):
        dates=pd.date_range('2024-01-01',periods=253)
        r=beta_metrics(dates,[100]*253,pd.Series(np.linspace(-.02,.02,252),index=dates[1:]))
        self.assertEqual(r['beta'],0);self.assertIsNone(r['correlation'])
    def test_dividend_offsets_ex_price_drop(self):
        days=(date(2024,1,2),date(2024,1,3));event=Dividend('510300',date(2024,1,1),days[0],days[1],date(2024,1,4),D(1))
        data=Dataset(days,{'510300':{d:RawBar(d,D(p),D(p),D(p),D(p)) for d,p in zip(days,['10','9'])}},(event,),{})
        self.assertEqual(benchmark_returns(data,'510300').iloc[0],0)
    def test_stress_cash_unchanged(self):
        r=exposure_stress(100000,{'510300':50000,'511010':40000},[dict(name='both',**{'510300':-.2,'511010':-.05})])[0]
        self.assertEqual(D(r['pnl']),-12000);self.assertEqual(D(r['ending_equity']),88000)
        with self.assertRaises(ValueError):exposure_stress(100,{'510300':50,'511010':40},[dict(name='invalid',**{'510300':-1.1,'511010':0})])
    def test_disclosure_is_partial_and_dated(self):
        d=json.loads((Path(__file__).resolve().parents[1]/'data/reference/holdings_2026q3.json').read_text())
        self.assertTrue(d['not_current_holdings']);self.assertTrue(d['not_historical_holdings_series'])
        for fund in d['funds'].values():
            self.assertIsNone(fund['full_security_hhi'])
            self.assertGreater(D(fund['unlisted_security_nav_fraction']),0)
            self.assertEqual(fund['report_date'],'2026-09-30')
            self.assertLess(D(fund['listed_nav_fraction']),D(fund['security_nav_fraction']))
if __name__=='__main__':unittest.main()
