"""Synthetic accounting scenarios with dates/amount from one verified notice.

Prices, opening cash and order sizes below are synthetic unit-test inputs,
not downloaded quotes and never a backtest or a return claim.
"""
import unittest,json
from pathlib import Path
from datetime import date,timedelta
from decimal import Decimal as D
from etf_research.accounting import Ledger,Dividend,Costs
F=json.loads(Path(__file__).with_name('dividend_fixture.json').read_text())
EVENT=Dividend('510300',date(2026,1,12),date.fromisoformat(F['record_date']),date.fromisoformat(F['ex_date']),date.fromisoformat(F['pay_date']),D(F['per_share']))
SESSIONS=[date(2026,1,d) for d in [15,16,19,20,21,22,23,26,27,28]]
FREE=Costs(D(0),D(0),D(0),D(0))
def ledger(cash=0,units=100,costs=FREE):
 return Ledger(SESSIONS,[EVENT],cash=D(cash),holdings={'510300':units},costs=costs,lot_size=100)
def advance(l,day):
 while l.cursor+1<len(l.sessions) and l.sessions[l.cursor+1]<=day:
  if l.is_open:l.close_session()
  l.open_session(l.sessions[l.cursor+1])

class AccountingTests(unittest.TestCase):
 def test_receivable_then_payment_then_available(self):
  l=ledger();advance(l,date(2026,1,19))
  self.assertEqual(l.receivables[EVENT.key],D('12.3'));self.assertEqual(l.cash,0)
  with self.assertRaises(ValueError):l.trade('510300','buy',100,D('.01'),signal_date=date(2026,1,16))
  advance(l,date(2026,1,27));self.assertEqual(l.cash,D('12.3'));self.assertEqual(l.available_cash,0);self.assertFalse(l.receivables)
  with self.assertRaises(ValueError):l.trade('510300','buy',100,D('.01'),signal_date=date(2026,1,26))
  advance(l,date(2026,1,28));self.assertEqual(l.available_cash,D('12.3'))
  l.trade('510300','buy',100,D('.01'),signal_date=date(2026,1,27));self.assertEqual(l.cash,D('11.3'))
 def test_selling_on_ex_date_keeps_recorded_entitlement(self):
  l=ledger();advance(l,date(2026,1,19));l.trade('510300','sell',100,D(4),signal_date=date(2026,1,16))
  advance(l,date(2026,1,28));self.assertEqual(l.cash,D('412.3'));self.assertEqual(l.holdings['510300'],0)
 def test_ex_date_buy_does_not_receive_dividend(self):
  l=ledger(1000,0);advance(l,date(2026,1,19));l.trade('510300','buy',100,D(4),signal_date=date(2026,1,16))
  advance(l,date(2026,1,28));self.assertEqual(l.cash,600)
 def test_record_day_purchase_qualifies(self):
  l=ledger(1000,0);advance(l,date(2026,1,16));l.trade('510300','buy',100,D(4),signal_date=date(2026,1,15))
  advance(l,date(2026,1,19));self.assertEqual(l.receivables[EVENT.key],D('12.3'))
 def test_equity_no_dividend_double_count(self):
  l=ledger();advance(l,date(2026,1,16));before=l.equity({'510300':D(4)})
  advance(l,date(2026,1,19));self.assertEqual(l.equity({'510300':D('3.877')}),before)
  advance(l,date(2026,1,27));self.assertEqual(l.equity({'510300':D('3.877')}),before)
 def test_same_day_future_and_unknown_signals_rejected(self):
  l=ledger(1000);advance(l,date(2026,1,19))
  for signal in [date(2026,1,19),date(2026,1,20),date(2026,1,18)]:
   with self.assertRaises(ValueError):l.trade('510300','buy',100,D(4),signal_date=signal)
  self.assertEqual(l.cash,1000)
 def test_commission_minimum_and_adverse_slippage(self):
  costs=Costs(D('.001'),D(5),D(50),D(0));l=ledger(1000,0,costs);advance(l,date(2026,1,16))
  r=l.trade('510300','buy',100,D(4),signal_date=date(2026,1,15))
  self.assertEqual(r['fill_price'],D('4.02'));self.assertEqual(r['commission'],5);self.assertEqual(l.cash,593)
 def test_sale_fee_slippage_and_tax(self):
  costs=Costs(D('.01'),D(0),D(50),D('.001'));l=ledger(0,100,costs);advance(l,date(2026,1,16))
  r=l.trade('510300','sell',100,D(4),signal_date=date(2026,1,15))
  self.assertEqual(r['notional'],398);self.assertEqual(r['tax'],D('.398'));self.assertEqual(l.cash,D('393.622'))
 def test_no_skipped_or_duplicate_sessions(self):
  l=ledger()
  with self.assertRaises(ValueError):l.open_session(date(2026,1,16))
  l.open_session(SESSIONS[0])
  with self.assertRaises(ValueError):l.open_session(SESSIONS[0])
  l.close_session()
  with self.assertRaises(ValueError):l.open_session(SESSIONS[0])
 def test_reject_incomplete_start_and_duplicate_event(self):
  with self.assertRaises(ValueError):Ledger(SESSIONS[2:],[EVENT],cash=0,holdings={},costs=FREE,lot_size=100)
  with self.assertRaises(ValueError):Ledger(SESSIONS,[EVENT,EVENT],cash=0,holdings={},costs=FREE,lot_size=100)
 def test_reject_nonfinite_float_and_short_sale(self):
  l=ledger(1000,0);advance(l,date(2026,1,16))
  for price in [D('NaN'),D('Infinity'),D(-1),4.0]:
   with self.assertRaises((ValueError,TypeError)):l.trade('510300','buy',100,price,signal_date=SESSIONS[0])
  with self.assertRaises(ValueError):l.trade('510300','sell',100,D(4),signal_date=SESSIONS[0])
 def test_same_session_buy_cannot_be_resold(self):
  l=ledger(1000,0);advance(l,date(2026,1,16));l.trade('510300','buy',100,D(4),signal_date=date(2026,1,15))
  with self.assertRaises(ValueError):l.trade('510300','sell',100,D(4),signal_date=date(2026,1,15))
  advance(l,date(2026,1,19));l.trade('510300','sell',100,D(4),signal_date=date(2026,1,16))
  self.assertEqual(l.holdings['510300'],0)
 def test_end_before_pay_keeps_receivable(self):
  l=Ledger(SESSIONS[:5],[EVENT],cash=0,holdings={'510300':100},costs=FREE,lot_size=100)
  advance(l,SESSIONS[4]);l.close_session();self.assertEqual(l.cash,0);self.assertEqual(l.equity({'510300':D(4)}),D('412.3'))
if __name__=='__main__':unittest.main()
