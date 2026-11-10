"""Descriptive windows of continuous NAV; never label retrospective data unseen."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,argparse
from datetime import date
p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);a=p.parse_args();out=[]
for f in sorted(a.results.glob('*_daily.csv')):
 rows=list(csv.DictReader(f.open()))
 def window(start,end):
  first,last=rows[start],rows[end];days=(date.fromisoformat(last['date'])-date.fromisoformat(first['date'])).days
  ratio=D(last['equity'])/D(first['equity']);peak=D(first['equity']);dd=D(0)
  for r in rows[start:end+1]:
   nav=D(r['equity']);peak=max(peak,nav);dd=min(dd,nav/peak-1)
  return {'start':first['date'],'end':last['date'],'trading_intervals':end-start,'total_return':float(ratio-1),'annualized_return':float(ratio**(D('365.25')/days)-1),'max_close_drawdown':float(dd)}
 rolling=[window(i-252,i) for i in range(252,len(rows))]
 # 252 initial trading intervals reserved as warm-up/early history; no fitting.
 # Keep ongoing positions and costs; do not invent cost-free resets at boundaries.
 blocks=[window(i,min(i+126,len(rows)-1)) for i in range(252,len(rows)-1,126)]
 vals=[w['annualized_return'] for w in rolling]
 out.append({'run':f.stem.removesuffix('_daily'),'rolling_252':rolling,'rolling_summary':{'count':len(vals),'minimum':min(vals),'maximum':max(vals),'fraction_at_least_4pct':sum(v>=.04 for v in vals)/len(vals),'fraction_at_least_5pct':sum(v>=.05 for v in vals)/len(vals)},'post_252_nonoverlapping_blocks':blocks})
(a.results/'windows.json').write_text(json.dumps({'interpretation':'Retrospective continuous-portfolio diagnostics. Overlapping windows are dependent; frequencies are not probabilities. No parameter optimization, no untouched out-of-sample claim. Final short block separately labeled by interval count.','runs':out},indent=2))
for r in out:
 if r['run'].endswith('_base'):print(r['run'],r['rolling_summary'])
