import unittest
from decimal import Decimal as D
from pathlib import Path
from dataclasses import replace
from etf_research.data import load_dataset
from etf_research.baselines import run
from etf_research.evaluation import metrics,chronological_folds
class EvaluationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load_dataset(Path(__file__).resolve().parents[1]/'data/snapshots');cls.result=run(cls.data,'monthly_50_50','base')
 def test_folds_cover_each_post_warmup_interval_once(self):
  d=self.data;e=chronological_folds(self.result);folds=e['folds']
  self.assertEqual([f['trading_intervals'] for f in folds],[126,126,126,9]);self.assertTrue(folds[-1]['partial_fold'])
  self.assertEqual(sum(f['trade_count'] for f in folds),sum(t['kind']=='trade' and t['day']>d.sessions[252] for t in self.result['journal']))
  for f in folds:self.assertLess(f['information_window_end'],f['test_first_session']);self.assertEqual(f['information_window_end'],f['anchor_date']);self.assertFalse(f['parameters_fitted'])
 def test_fold_returns_compound_to_continuous_post_warmup_nav(self):
  e=chronological_folds(self.result);product=D(1)
  for f in e['folds']:product*=D(f['ending_equity'])/D(f['starting_equity'])
  self.assertAlmostEqual(float(product-1),e['post_warmup_metrics']['total_return'],places=12)
 def test_future_changes_do_not_change_completed_fold(self):
  d=self.data;cut=d.sessions[378];bars={s:{day:(replace(b,open=b.open*2,high=b.high*2,low=b.low*2,close=b.close*2) if day>cut else b) for day,b in v.items()} for s,v in d.bars.items()}
  changed=run(replace(d,bars=bars),'monthly_50_50','base')
  self.assertEqual(chronological_folds(self.result)['folds'][0],chronological_folds(changed)['folds'][0])
 def test_metrics_matches_independent_endpoints_and_drawdown(self):
  rows=self.result['daily'];m=metrics(rows);nav=[float(r['equity']) for r in rows]
  dd=min(v/max(nav[:i+1])-1 for i,v in enumerate(nav))
  self.assertAlmostEqual(m['total_return'],nav[-1]/nav[0]-1,places=12);self.assertAlmostEqual(m['max_close_drawdown'],dd,places=12)
 def test_invalid_fold_lengths_rejected(self):
  for value in [0,-1,True,1.5]:
   with self.assertRaises(ValueError):chronological_folds(self.result,train_intervals=value)
