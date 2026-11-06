"""Previous-data-only targets for the first executable forward session.

No orders, prices for the target day, or fills are created. This deliberately
supports only the first execution day; later rebalance planning needs review.
"""
from datetime import date,datetime,time,timedelta
from decimal import Decimal as D
from zoneinfo import ZoneInfo
from .baselines import STRATEGIES,SCENARIOS,targets,trend_weights
from .forward import advance,START,digest,engine_digest,prefix_digest
from .admission import sessions_between

class PriorSignals:
 def __init__(self,data,day):self.data=data;self.day=day
 def history_before_open(self,symbol,day):
  if day!=self.day:raise ValueError('Wrong signal day')
  return tuple(self.data.bars[symbol][d] for d in self.data.sessions if d<day)
 def events_known_before_open(self,day):
  if day!=self.day:raise ValueError('Wrong signal day')
  return tuple(e for e in self.data.dividends if e.announcement_date<day)

def prepare(data,checkpoint,holiday_ranges,*,now):
 if now.tzinfo is None:raise ValueError('Timezone-aware creation time required')
 local=now.astimezone(ZoneInfo('Asia/Shanghai'));day=local.date()
 if checkpoint.get('forward_sessions')!=1 or checkpoint.get('as_of')!=str(START):raise ValueError('Only first executable forward day supported')
 if data.sessions[-1]!=START or any(d>=day for d in data.sessions):raise ValueError('Only previous completed inputs allowed')
 upcoming=sessions_between(holiday_ranges,START+timedelta(days=1),day)
 if upcoming!=(day,):raise ValueError('Target must be the next independently verified exchange day')
 if local.time()>=time(9,30):raise ValueError('Continuous trading has started; do not create a pre-continuous plan')
 if advance(data,checkpoint,now=now)!=checkpoint:raise ValueError('Checkpoint replay mismatch')
 prices={s:data.bars[s][START].close for s in data.bars};portfolios={}
 for strategy,(weights,monthly) in STRATEGIES.items():
  if strategy=='trend_120':weights=trend_weights(PriorSignals(data,day),day)
  if weights is None:raise ValueError('Missing trend warmup')
  for scenario in SCENARIOS:
   name=strategy+'_'+scenario;prior=checkpoint['portfolios'][name]['summary']
   if prior['trades'] or any(prior['ending_holdings'].values()):raise ValueError('First-day checkpoint must hold no positions')
   equity=D(prior['ending_equity']);planned=targets(weights,equity,prices)
   portfolios[name]={'signal_date':str(START),'weights':{s:str(v) for s,v in weights.items()},'target_units':planned,'previous_equity':str(equity),'previous_holdings':prior['ending_holdings'],'actual_fills':None}
 result={'format':1,'created_at_shanghai':local.isoformat(),'target_session':str(day),'source_through':str(START),'created_before_opening_auction':local.time()<time(9,15),'created_before_continuous_trading':True,'protocol_commit':checkpoint['protocol_commit'],'checkpoint_sha256':checkpoint['checkpoint_sha256'],'engine_sha256':engine_digest(),'admitted_prefix_sha256':prefix_digest(data,START),'previous_closes':{s:str(v) for s,v in prices.items()},'portfolios':portfolios,'real_money':False,'execution_authorized':False,'price_or_return_for_target_day_used':False,'scope':'Fixed first-execution-day target shares only. Closing admission, announcement review, opening-price guards, fees and cash constraints still determine simulated fills. No broker orders.'}
 result['plan_sha256']=digest(result);return result

def check_execution(plan,checkpoint):
 """Compare actual research decisions after close; never changes the ledger."""
 if digest({k:v for k,v in plan.items() if k!='plan_sha256'})!=plan.get('plan_sha256'):raise ValueError('Plan checksum mismatch')
 if digest({k:v for k,v in checkpoint.items() if k!='checkpoint_sha256'})!=checkpoint.get('checkpoint_sha256'):raise ValueError('Checkpoint checksum mismatch')
 if checkpoint['engine_sha256']!=plan['engine_sha256'] or checkpoint['protocol_commit']!=plan['protocol_commit']:raise ValueError('Plan engine/protocol mismatch')
 if checkpoint['as_of']<plan['target_session']:raise ValueError('Target session has not been admitted')
 if set(checkpoint['portfolios'])!=set(plan['portfolios']):raise ValueError('Portfolio coverage mismatch')
 count=0
 for name,p in plan['portfolios'].items():
  decisions=[d for d in checkpoint['portfolios'][name]['decisions'] if d['day']==plan['target_session']]
  expected={s for s,n in p['target_units'].items() if n!=p['previous_holdings'].get(s,0)}
  if {d['symbol'] for d in decisions}!=expected or len(decisions)!=len(expected):raise ValueError('Planned decision coverage mismatch')
  for d in decisions:
   if d['target_units']!=p['target_units'][d['symbol']] or d['signal_date']!=p['signal_date']:raise ValueError('Executed target differs from saved plan')
   count+=1
 return {'target_session':plan['target_session'],'portfolios_checked':len(plan['portfolios']),'decisions_checked':count,'target_units_match':True,'scope':'Compares intended targets, not a claim that every target was filled.'}
