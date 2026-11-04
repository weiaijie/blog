import unittest
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
from etf_research.data import load_dataset
from etf_research.baselines import run,targets,guard_reason,STRATEGIES,SCENARIOS

class BaselineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load_dataset(Path(__file__).resolve().parents[1]/'data/snapshots')
 def test_cash_has_no_return_no_trade(self):
  r=run(self.data,'cash','high');self.assertEqual(r['summary']['total_return'],0);self.assertEqual(r['summary']['trades'],0)
 def test_target_rounding_and_no_leverage(self):
  marks={'510300':D(4),'511010':D(140)};w={'510300':D('.2'),'511010':D('.8')}
  t=targets(w,D(100000),marks);self.assertEqual(t,{'510300':5000,'511010':500});self.assertLessEqual(sum(t[s]*marks[s] for s in t),100000)
 def test_ex_day_and_open_or_slippage_buffer(self):
  self.assertEqual(guard_reason(D(4),D(4),D(4),ex_day=True),'known_ex_dividend_day')
  self.assertEqual(guard_reason(D('4.36'),D(4),D('4.36'),ex_day=False),'conservative_9pct_buffer')
  self.assertIsNotNone(guard_reason(D('4.35'),D(4),D('4.36'),ex_day=False))
  self.assertIsNone(guard_reason(D(4),D(4),D('4.001'),ex_day=False))
 def test_future_mutation_and_prefix_replay(self):
  d=self.data;cut=d.sessions[320];base=run(d,'monthly_50_50','base')
  bars={s:{day:(replace(b,open=b.open*2,high=b.high*2,low=b.low*2,close=b.close*2) if day>cut else b) for day,b in v.items()} for s,v in d.bars.items()}
  changed=run(replace(d,bars=bars),'monthly_50_50','base')
  short=replace(d,sessions=d.sessions[:321],bars={s:{day:b for day,b in v.items() if day<=cut} for s,v in d.bars.items()})
  prefix=run(short,'monthly_50_50','base')
  for key in ['daily','decisions','journal']:
   field='date' if key=='daily' else 'day'
   expected=[r for r in base[key] if r[field]<=cut]
   self.assertEqual(expected,[r for r in changed[key] if r[field]<=cut]);self.assertEqual(expected,prefix[key])
 def test_today_close_high_low_do_not_change_today_order(self):
  d=self.data;day=d.sessions[1];base=run(d,'monthly_50_50','base')
  bars={s:dict(v) for s,v in d.bars.items()}
  for s in bars:bars[s][day]=replace(bars[s][day],close=D(999),high=D(999),low=D('.001'))
  changed=run(replace(d,bars=bars),'monthly_50_50','base')
  self.assertEqual([r for r in base['decisions'] if r['day']==day],[r for r in changed['decisions'] if r['day']==day])
 def test_buy_hold_higher_cost_reduces_ending_value(self):
  for strategy in ['equity_hold','bond_hold']:
   values=[D(run(self.data,strategy,s)['summary']['ending_equity']) for s in ['low','base','high']]
   self.assertEqual(values,sorted(values,reverse=True));self.assertGreater(values[0],values[-1])
 def test_all_scenarios_independent_cash_shares_and_dividends(self):
  d=self.data
  for strategy in STRATEGIES:
   for scenario in SCENARIOS:
    r=run(d,strategy,scenario);trades=[t for t in r['journal'] if t['kind']=='trade']
    def units_at(s,day):return sum(t['units']*(1 if t['side']=='buy' else -1) for t in trades if t['symbol']==s and t['day']<=day)
    ent={e.key:units_at(e.symbol,e.record_date)*e.per_share for e in d.dividends}
    for row in r['daily']:
     day=row['date'];cash=D(100000)
     for t in trades:
      if t['day']<=day:cash+=(t['notional'] if t['side']=='sell' else -t['notional'])-t['commission']-t['tax']
     cash+=sum((ent[e.key] for e in d.dividends if e.pay_date<=day),D(0))
     rec=sum((ent[e.key] for e in d.dividends if e.ex_date<=day<e.pay_date),D(0))
     blocked=sum((ent[e.key] for e in d.dividends if e.pay_date==day),D(0))
     equity=cash+rec+sum(units_at(s,day)*d.bars[s][day].close for s in d.bars)
     self.assertEqual((row['cash'],row['available_cash'],row['receivables'],row['equity']),(cash,cash-blocked,rec,equity))
     for s in d.bars:self.assertEqual(row['units_'+s],units_at(s,day))
    self.assertTrue(all(t['signal_date']<t['day'] for t in trades))
 def test_no_terminal_liquidation_claim(self):
  r=run(self.data,'equity_hold','base');self.assertFalse(r['summary']['terminal_liquidation_included']);self.assertGreater(r['daily'][-1]['units_510300'],0)
if __name__=='__main__':unittest.main()

class TrendTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load_dataset(Path(__file__).resolve().parents[1]/'data/snapshots')
 def test_trend_requires_120_prior_closes(self):
  from etf_research.baselines import trend_weights
  d=self.data;self.assertIsNone(trend_weights(d,d.sessions[119]));self.assertIsNotNone(trend_weights(d,d.sessions[120]))
  r=run(d,'trend_120','base');self.assertTrue(all(x['day']>=d.sessions[120] for x in r['decisions']))
 def test_trend_prefix_invariance(self):
  d=self.data;cut=d.sessions[400];full=run(d,'trend_120','base')
  short=replace(d,sessions=d.sessions[:401],bars={s:{day:b for day,b in v.items() if day<=cut} for s,v in d.bars.items()})
  r=run(short,'trend_120','base')
  for key,field in [('daily','date'),('journal','day'),('decisions','day')]:self.assertEqual([x for x in full[key] if x[field]<=cut],r[key])
 def test_trend_dividend_ex_day_does_not_create_false_price_drop(self):
  from etf_research.baselines import trend_weights
  from etf_research.data import Dataset,RawBar
  from etf_research.accounting import Dividend
  from datetime import date,timedelta
  days=tuple(date(2024,1,1)+timedelta(days=i) for i in range(122))
  bars={day:RawBar(day,D(100),D(100),D(100),D(100)) for day in days}
  # Flat total return: cash distribution offsets price fall exactly.
  for day in days[100:]:bars[day]=RawBar(day,D(90),D(90),D(90),D(90))
  event=Dividend('510300',days[98],days[99],days[100],days[101],D(10))
  data=Dataset(days,{'510300':bars},(event,),{})
  self.assertEqual(trend_weights(data,days[120])['510300'],D(0))
  # Add actual capital appreciation after ex-date: risk-on.
  bars[days[119]]=replace(bars[days[119]],close=D(91))
  self.assertEqual(trend_weights(data,days[120])['510300'],D('.5'))
