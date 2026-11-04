import unittest
from decimal import Decimal as D
from dataclasses import replace
from pathlib import Path
from etf_research.data import load_dataset
from etf_research.baselines import run

class ExecutionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load_dataset(Path(__file__).resolve().parents[1]/'data/snapshots')
 def test_delay_preserves_signal_target_and_uses_later_open(self):
  d=self.data;one=run(d,'monthly_50_50','base');three=run(d,'monthly_50_50','base',execution_delay=3)
  a=[x for x in one['decisions'] if x['day']==d.sessions[1]];b=[x for x in three['decisions'] if x['day']==d.sessions[3]]
  self.assertEqual([(x['symbol'],x['signal_date'],x['target_units']) for x in a],[(x['symbol'],x['signal_date'],x['target_units']) for x in b])
  trades=[x for x in three['journal'] if x['kind']=='trade']
  for t in trades:self.assertEqual(t['raw_price'],d.bars[t['symbol']][t['day']].open);self.assertEqual(d.sessions.index(t['day'])-d.sessions.index(t['signal_date']),3)
 def test_pending_order_not_filled_after_sample_end(self):
  d=replace(self.data,sessions=self.data.sessions[:3]);r=run(d,'equity_hold','base',execution_delay=3)
  self.assertEqual(r['summary']['trades'],0);self.assertEqual(r['summary']['pending_target_batches_at_end'],1);self.assertEqual(r['summary']['total_return'],0)
 def test_small_capital_cannot_buy_bond_lot(self):
  r=run(self.data,'bond_hold','base',D(10000));self.assertEqual(r['summary']['trades'],0);self.assertEqual(r['summary']['total_return'],0)
 def test_delay_prefix_invariance(self):
  d=self.data;cut=d.sessions[300];a=run(d,'trend_120','base',execution_delay=3)
  b=run(replace(d,sessions=d.sessions[:301]),'trend_120','base',execution_delay=3)
  for key,field in [('daily','date'),('decisions','day'),('journal','day')]:self.assertEqual([r for r in a[key] if r[field]<=cut],b[key])
 def test_bad_inputs_rejected(self):
  for delay in [0,4,True,1.5]:
   with self.assertRaises(ValueError):run(self.data,'cash','base',execution_delay=delay)
  for initial in [D(0),D(-1),D('NaN'),10000]:
   with self.assertRaises(ValueError):run(self.data,'cash','base',initial)
