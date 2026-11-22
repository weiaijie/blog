"""Independent endpoint accounting and post-hoc daily-bar fill diagnostics."""
from pathlib import Path
from decimal import Decimal as D
import json,argparse
from etf_research.data import load_dataset
from etf_research.long_history import load_long_history
p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);m=p.add_mutually_exclusive_group();m.add_argument('--extended',action='store_true');m.add_argument('--long-history',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[1];data=load_long_history(root/'data/snapshots') if a.long_history else load_dataset(root/'data/snapshots',extended=a.extended)
summaries=json.loads((a.results/'sensitivity.json').read_text())['results'];audits=json.loads((a.results/'audit.json').read_text());end=str(data.sessions[-1]);output=[]
for r in summaries:
 trades=[t for t in audits[r['run']]['journal'] if t['kind']=='trade'];cash=D(r['initial_cash']);units={s:0 for s in data.bars};outside=[]
 for t in trades:
  sign=1 if t['side']=='buy' else -1;units[t['symbol']]+=sign*t['units'];cash-=sign*D(t['notional'])+D(t['commission'])+D(t['tax'])
  bar=next(b for day,b in data.bars[t['symbol']].items() if str(day)==t['day'])
  if not bar.low<=D(t['fill_price'])<=bar.high:outside.append({'day':t['day'],'symbol':t['symbol'],'fill_price':t['fill_price'],'low':str(bar.low),'high':str(bar.high)})
 rec=D(0)
 for e in data.dividends:
  held=sum(t['units']*(1 if t['side']=='buy' else -1) for t in trades if t['symbol']==e.symbol and t['day']<=str(e.record_date));amount=held*e.per_share
  if str(e.pay_date)<=end:cash+=amount
  elif str(e.ex_date)<=end:rec+=amount
 equity=cash+rec+sum(n*data.bars[s][data.sessions[-1]].close for s,n in units.items())
 assert cash==D(r['ending_cash']) and equity==D(r['ending_equity']),r['run']
 for s,n in units.items():assert n==r['ending_holdings'].get(s,0)
 assert sum((D(t['commission']) for t in trades),D(0))==D(r['commissions'])
 output.append({'run':r['run'],'endpoint_accounting_passed':True,'fills_outside_daily_range':len(outside),'examples':outside[:5]})
report={'independent_endpoint_checks':len(output),'all_passed':True,'range_check_is_posthoc_only':True,'range_check_used_to_change_orders':False,'interpretation':'Slipped fill prices are cost-model prices and can fall outside observed daily high/low; these are not actual fills. This diagnostic never uses future H/L to select orders.','runs':output}
(a.results/'execution_diagnostics.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS independent endpoints:',len(output),'; cost-model fills outside daily range:',sum(x['fills_outside_daily_range'] for x in output))
