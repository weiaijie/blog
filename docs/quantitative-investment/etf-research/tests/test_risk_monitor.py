import copy,json,unittest
from pathlib import Path
import numpy as np
import pandas as pd
from etf_research.risk_monitor import analyze,load_config
ROOT=Path(__file__).resolve().parents[1]
class RiskMonitorTests(unittest.TestCase):
 def setUp(self):self.r=json.loads((ROOT/'config/research.json').read_text())['risk']
 def test_year_boundary_uses_previous_close(self):
  x=analyze(['2024-12-31','2025-01-02'],[100,80],self.r)
  self.assertAlmostEqual(x['years'][-1]['max_drawdown'],.2);self.assertTrue(x['years'][-1]['limit_breached'])
 def test_current_recovery_not_historical_warning(self):
  x=analyze(['2024-01-01','2024-02-01','2024-03-01'],[100,70,110],self.r)
  self.assertAlmostEqual(x['max_close_drawdown'],.3);self.assertEqual(x['current_drawdown'],0)
  self.assertNotIn('current_drawdown_warning',x['alerts']);self.assertIn('observed_year_drawdown_limit',x['alerts'])
 def test_insufficient_forward_window_is_null(self):
  x=analyze(['2026-11-05'],[100000],self.r)
  for k in ['rolling_volatility','rolling_sharpe','daily_var','annualized_return','latest_daily_return']:self.assertIsNone(x[k])
 def test_flat_series_sharpe_undefined(self):
  x=analyze(pd.date_range('2024-01-01',periods=253),np.ones(253)*100,self.r)
  self.assertEqual(x['rolling_volatility'],0);self.assertEqual(x['daily_var'],0);self.assertIsNone(x['rolling_sharpe'])
 def test_exact_window_and_hand_calculated_metrics(self):
  r=copy.deepcopy(self.r);r['lookback_returns']=3
  x=analyze(pd.date_range('2024-01-01',periods=4),[100,110,99,99],r)
  self.assertAlmostEqual(x['rolling_volatility'],.1*np.sqrt(252));self.assertAlmostEqual(x['daily_var'],.09);self.assertAlmostEqual(x['rolling_sharpe'],0)
 def test_duplicate_unsorted_invalid_nav_rejected(self):
  for dates,values in [(['2024-01-01']*2,[1,2]),(['2024-02-01','2024-01-01'],[1,2]),(['2024-01-01'],[np.nan]),(['2024-01-01'],[0])]:
   with self.assertRaises(ValueError):analyze(dates,values,self.r)
 def test_configuration_changes_monitor_not_input(self):
  values=[100,84];r=copy.deepcopy(self.r);r['drawdown_warning']=.18
  a=analyze(['2024-01-01','2024-01-02'],values,self.r);b=analyze(['2024-01-01','2024-01-02'],values,r)
  self.assertIn('current_drawdown_warning',a['alerts']);self.assertNotIn('current_drawdown_warning',b['alerts']);self.assertEqual(values,[100,84])
 def test_config_rejects_execution_and_bad_ranges(self):
  import tempfile
  config=json.loads((ROOT/'config/research.json').read_text())
  for key,value in [('action','trade'),('drawdown_warning',.5),('lookback_returns',True),('daily_var_limit',float('nan'))]:
   c=copy.deepcopy(config);c['risk'][key]=value
   with tempfile.TemporaryDirectory() as t:
    p=Path(t)/'config.json';p.write_text(json.dumps(c))
    with self.assertRaises(ValueError):load_config(p,ROOT)
 def test_yearly_peak_does_not_carry_old_peak(self):
  x=analyze(['2023-01-01','2023-12-31','2024-01-02'],[100,70,69],self.r)
  self.assertAlmostEqual(x['years'][-1]['max_drawdown'],1-69/70);self.assertFalse(x['years'][-1]['limit_breached'])
if __name__=='__main__':unittest.main()
