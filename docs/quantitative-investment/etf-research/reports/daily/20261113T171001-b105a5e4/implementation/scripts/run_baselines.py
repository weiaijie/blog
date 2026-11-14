"""Export frozen baseline scenarios with all orders and daily balances."""
from pathlib import Path
import argparse,csv,json
from etf_research.data import load_dataset
from etf_research.baselines import run,STRATEGIES,SCENARIOS
p=argparse.ArgumentParser();p.add_argument('--snapshots',type=Path,default=Path(__file__).resolve().parents[1]/'data/snapshots');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
d=load_dataset(a.snapshots);a.output.mkdir(parents=True,exist_ok=True);summaries=[]
for strategy in STRATEGIES:
 for scenario in SCENARIOS:
  r=run(d,strategy,scenario);name=strategy+'_'+scenario;summaries.append(r['summary'])
  with (a.output/(name+'_daily.csv')).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=r['daily'][0].keys());w.writeheader();w.writerows(r['daily'])
  (a.output/(name+'_audit.json')).write_text(json.dumps({k:v for k,v in r.items() if k!='daily'},default=str,indent=2))
(a.output/'results.json').write_text(json.dumps({'sample':d.provenance,'scenarios':{name:{k:str(v) for k,v in vars(c).items()} for name,c in SCENARIOS.items()},'results':summaries},indent=2))
for s in summaries:
 if s['scenario']=='base':print(s)
