"""Loader integrity, prefix-only views and trading-rule accounting contracts."""
import unittest,tempfile,shutil
from pathlib import Path
from datetime import date
from decimal import Decimal as D
from dataclasses import replace
from etf_research.data import load_dataset
from etf_research.accounting import Ledger,Costs,InstrumentRules
ROOT=Path(__file__).resolve().parents[1]/'data/snapshots'
RULES={'510300':InstrumentRules(100,D('.001'),False),'511010':InstrumentRules(100,D('.001'),True)}
S=[date(2026,1,15),date(2026,1,16),date(2026,1,19)]
FREE=Costs(D(0),D(0),D(0),D(0))
def make(costs=FREE):
 l=Ledger(S,[],cash=D(100000),holdings={},costs=costs,lot_size=100,instruments=RULES)
 l.open_session(S[0]);l.close_session();l.open_session(S[1]);return l

class RulesTests(unittest.TestCase):
 def test_bond_same_day_resale_allowed(self):
  l=make();l.trade('511010','buy',100,D(140),signal_date=S[0]);l.trade('511010','sell',100,D(140),signal_date=S[0]);self.assertEqual(l.cash,100000)
 def test_equity_same_day_resale_rejected(self):
  l=make();l.trade('510300','buy',100,D(4),signal_date=S[0])
  with self.assertRaises(ValueError):l.trade('510300','sell',100,D(4),signal_date=S[0])
 def test_unapproved_symbol_and_off_tick_and_off_lot_rejected(self):
  l=make()
  for symbol,n,price in [('X',100,D(4)),('510300',100,D('4.0001')),('510300',1,D(4))]:
   with self.assertRaises(ValueError):l.trade(symbol,'buy',n,price,signal_date=S[0])
  self.assertEqual(l.cash,100000)
 def test_slippage_rounded_adversely_to_tick(self):
  l=make(Costs(D(0),D(0),D(1),D(0)))
  r=l.trade('510300','buy',100,D('4.001'),signal_date=S[0]);self.assertEqual(r['fill_price'],D('4.002'))
 def test_fee_rounds_half_cent_up(self):
  l=make(Costs(D('.0000125'),D(0),D(0),D(0)))
  r=l.trade('510300','buy',100,D(4),signal_date=S[0]);self.assertEqual(r['commission'],D('.01'))

class DataTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load_dataset(ROOT)
 def test_real_dataset_shape_and_event_publication(self):
  d=self.data;self.assertEqual(len(d.sessions),640);self.assertEqual(len(d.dividends),7)
  self.assertEqual(str(d.sessions[0]),'2024-03-11');self.assertEqual(str(d.sessions[-1]),'2026-10-30')
  self.assertTrue(all(e.announcement_date<=e.record_date for e in d.dividends))
 def test_today_price_not_visible_before_open(self):
  d=self.data;day=d.sessions[100];history=d.history_before_open('510300',day)
  self.assertEqual(len(history),100);self.assertTrue(all(b.day<day and b.price_mode=='unadjusted' for b in history))
 def test_future_bar_change_does_not_affect_prefix(self):
  d=self.data;day=d.sessions[100];before=d.history_before_open('510300',day)
  bars={s:dict(v) for s,v in d.bars.items()};future=d.sessions[200]
  bars['510300'][future]=replace(bars['510300'][future],close=D(999))
  changed=replace(d,bars=bars);self.assertEqual(changed.history_before_open('510300',day),before)
 def test_announcement_day_excluded_until_next_session(self):
  d=self.data;e=next(e for e in d.dividends if e.symbol=='510300' and str(e.ex_date)=='2026-01-19')
  self.assertNotIn(e,d.events_known_before_open(e.announcement_date))
  nextday=next(day for day in d.sessions if day>e.announcement_date)
  self.assertIn(e,d.events_known_before_open(nextday))
 def test_tampered_raw_price_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   dst=Path(temp)/'snapshots';shutil.copytree(ROOT,dst)
   f=dst/'2026-11-02/sina_daily_510300.body';f.write_bytes(f.read_bytes()+b'\n')
   with self.assertRaisesRegex(ValueError,'hash mismatch'):load_dataset(dst)
 def test_tampered_official_pdf_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   dst=Path(temp)/'snapshots';shutil.copytree(ROOT,dst)
   f=dst/'2026-11-03-official-01/510300_20260112.pdf';f.write_bytes(f.read_bytes()+b'broken')
   with self.assertRaisesRegex(ValueError,'hash mismatch'):load_dataset(dst)
if __name__=='__main__':unittest.main()
