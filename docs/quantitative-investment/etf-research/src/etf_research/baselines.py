"""Daily-bar scenario baselines; no broker or executable-fill claim."""
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from .accounting import Ledger, Costs, InstrumentRules

SYMBOLS=('510300','511010')
RULES={s:InstrumentRules(100,D('.001'),s=='511010') for s in SYMBOLS}
SCENARIOS={
 'low':Costs(D('.0001'),D('5'),D('1'),D('0')),
 'base':Costs(D('.0003'),D('5'),D('5'),D('0')),
 'high':Costs(D('.001'),D('5'),D('10'),D('0')),
}
STRATEGIES={
 'cash':({'510300':D(0),'511010':D(0)},False),
 'equity_hold':({'510300':D(1),'511010':D(0)},False),
 'bond_hold':({'510300':D(0),'511010':D(1)},False),
 'monthly_20_80':({'510300':D('.2'),'511010':D('.8')},True),
 'monthly_50_50':({'510300':D('.5'),'511010':D('.5')},True),
 'trend_120':({'510300':D('.5'),'511010':D('.5')},True),
}

def trend_weights(data, day):
 """Fixed 120-close total-return trend, using only prior bars/known events.

 Signal index assumes fractional dividend reinvestment for comparison only;
 the portfolio still uses the actual receivable/cash/lot-size ledger.
 """
 history=data.history_before_open('510300',day)
 if len(history)<120:return None
 events=data.events_known_before_open(day)
 index=[D(1)]
 for prev,bar in zip(history,history[1:]):
  dividend=sum((e.per_share for e in events if e.symbol=='510300' and e.ex_date==bar.day),D(0))
  index.append(index[-1]*(bar.close+dividend)/prev.close)
 risk_on=index[-1]>sum(index[-120:],D(0))/120
 return {'510300':D('.5') if risk_on else D(0),'511010':D('.5') if risk_on else D(1)}

def targets(weights, equity, previous_marks):
 """Previous closing information only, rounded down to 100-share lots."""
 return {s:int(equity*weights[s]/previous_marks[s]/100)*100 for s in SYMBOLS}

def fill_price(raw, side, costs):
 rounding=ROUND_CEILING if side=='buy' else ROUND_FLOOR
 return (raw*(1+(1 if side=='buy' else -1)*costs.slippage_bps/10000)/D('.001')).to_integral_value(rounding=rounding)*D('.001')

def debit(units, fill, costs):
 notional=units*fill
 return notional+max(costs.minimum_commission,notional*costs.commission_rate).quantize(D('.01'),rounding=ROUND_HALF_UP)

def guard_reason(raw_open, previous_close, fill, *, ex_day):
 # Historical exact ex-reference and auction queues are not supplied.
 # Exclude known ex-days and moves >=9%. Research buffer, NOT exchange limit.
 if ex_day:return 'known_ex_dividend_day'
 if max(abs(raw_open/previous_close-1),abs(fill/previous_close-1))>=D('.09'):
  return 'conservative_9pct_buffer'
 return None

def run(data, strategy, scenario, initial=D('100000'), *, execution_delay=1):
 if type(execution_delay) is not int or execution_delay not in (1,2,3):
  raise ValueError('Execution delay must be 1, 2 or 3 sessions')
 if not isinstance(initial,D) or not initial.is_finite() or initial<=0:
  raise ValueError('Initial cash must be a positive finite Decimal')
 weights,monthly=STRATEGIES[strategy];costs=SCENARIOS[scenario]
 ledger=Ledger(data.sessions,data.dividends,cash=initial,holdings={},costs=costs,lot_size=100,instruments=RULES)
 rows=[];decisions=[];previous_equity=initial;previous_marks=None;pending={}
 for i,day in enumerate(data.sessions):
  first=120 if strategy=='trend_120' else 1
  due=i==first or (i>first and monthly and day.month!=data.sessions[i-1].month)
  if due and strategy=='trend_120':weights=trend_weights(data,day)
  if due:
   pending[i+execution_delay-1]=(targets(weights,previous_equity,previous_marks),data.sessions[i-1])
  order=pending.pop(i,None)
  planned,signal_date=order if order else (None,None)
  ledger.open_session(day)
  if planned is not None:
   known=data.events_known_before_open(day)
   for side in ('sell','buy'):
    for s in SYMBOLS:
     delta=planned[s]-ledger.holdings.get(s,0)
     if (side=='buy' and delta<=0) or (side=='sell' and delta>=0):continue
     units=abs(delta);raw=data.bars[s][day].open;fill=fill_price(raw,side,costs)
     reason=guard_reason(raw,previous_marks[s],fill,ex_day=any(e.symbol==s and e.ex_date==day for e in known))
     decision={'day':day,'signal_date':signal_date,'symbol':s,'side':side,'target_units':planned[s],'requested_units':units,'filled_units':0,'reason':reason}
     if reason is None:
      if side=='buy':
       units=min(units,int(ledger.available_cash/fill/100)*100)
       while units>0 and debit(units,fill,costs)>ledger.available_cash:units-=100
      if units:
       trade=ledger.trade(s,side,units,raw,signal_date=signal_date)
       assert trade['fill_price']==fill
       decision['filled_units']=units
      decision['reason']='filled' if units==abs(delta) else 'cash_limited_partial_or_zero'
     decisions.append(decision)
  ledger.close_session()
  marks={s:data.bars[s][day].close for s in SYMBOLS};equity=ledger.equity(marks)
  assert ledger.cash>=0 and ledger.available_cash>=0 and equity>0
  rows.append({'date':day,'equity':equity,'cash':ledger.cash,'available_cash':ledger.available_cash,'receivables':sum(ledger.receivables.values(),D(0)),**{'units_'+s:ledger.holdings.get(s,0) for s in SYMBOLS}})
  previous_equity=equity;previous_marks=marks
 trades=[r for r in ledger.journal if r['kind']=='trade']
 peak=initial;drawdown=D(0)
 for row in rows:
  peak=max(peak,row['equity']);drawdown=min(drawdown,row['equity']/peak-1)
 elapsed=(data.sessions[-1]-data.sessions[0]).days
 terminal=rows[-1]['equity'];total=terminal/initial-1
 summary={'strategy':strategy,'scenario':scenario,'initial_cash':str(initial),'ending_equity':str(terminal),'ending_cash':str(ledger.cash),'total_return':float(total),'annualized_scenario_return':float((terminal/initial)**(D('365.25')/elapsed)-1) if elapsed else None,'max_close_drawdown':float(drawdown),'trades':len(trades),'commissions':str(sum((r['commission'] for r in trades),D(0))),'sell_tax':str(sum((r['tax'] for r in trades),D(0))),'slippage_cost':str(sum((abs(r['fill_price']-r['raw_price'])*r['units'] for r in trades),D(0))),'excluded_orders':sum(d['reason'] in ('known_ex_dividend_day','conservative_9pct_buffer') for d in decisions),'cash_limited_orders':sum(d['reason']=='cash_limited_partial_or_zero' for d in decisions),'ending_holdings':dict(ledger.holdings),'terminal_liquidation_included':False}
 summary.update(execution_delay_sessions=execution_delay,pending_target_batches_at_end=len(pending))
 return {'summary':summary,'daily':rows,'decisions':decisions,'journal':ledger.journal}
