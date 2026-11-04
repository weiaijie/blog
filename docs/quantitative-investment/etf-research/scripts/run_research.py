"""Frozen 162-case execution sensitivity and chronological evaluation pipeline."""
from pathlib import Path
from decimal import Decimal as D
from datetime import date
import argparse,csv,json,hashlib
from etf_research.data import load_dataset
from etf_research.baselines import run,STRATEGIES,SCENARIOS
from etf_research.evaluation import chronological_folds
PROTOCOL_COMMIT='0c797f5ed5321d8653d64ccf0f795e1529f6f9b2'
def main():
 p=argparse.ArgumentParser();p.add_argument('--snapshots',type=Path,default=Path(__file__).resolve().parents[1]/'data/snapshots');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 d=load_dataset(a.snapshots);a.output.mkdir(parents=True,exist_ok=True)
 def save(name,value):(a.output/name).write_text(json.dumps(value,default=str,ensure_ascii=False,indent=2)+'\n')
 all_summaries=[];audits={};baseline=[];evaluations={}
 for strategy in STRATEGIES:
  for scenario in SCENARIOS:
   for capital in ['10000','100000','1000000']:
    for delay in [1,2,3]:
     result=run(d,strategy,scenario,D(capital),execution_delay=delay)
     name=f'{strategy}_{scenario}_{capital}_d{delay}';all_summaries.append({'run':name,**result['summary']})
     audits[name]={'decisions':result['decisions'],'journal':result['journal']}
     if capital=='100000' and delay==1:
      baseline.append({'run':name,**result['summary']});evaluations[name]=chronological_folds(result)
      with (a.output/(name+'_daily.csv')).open('w',newline='') as f:
       w=csv.DictWriter(f,fieldnames=result['daily'][0].keys());w.writeheader();w.writerows(result['daily'])
 # Freeze one code/data provenance record; observations beyond admitted cutoff excluded.
 save('results.json',{'protocol_commit':PROTOCOL_COMMIT,'sample':d.provenance,'initial_cash_main':'100000','execution_delay_main':1,'scenario_parameters':{k:{n:str(v) for n,v in vars(c).items()} for k,c in SCENARIOS.items()},'results':baseline})
 save('sensitivity.json',{'predeclared_matrix':{'capital':['10000','100000','1000000'],'delay_sessions':[1,2,3],'strategies':list(STRATEGIES),'costs':list(SCENARIOS)},'selection_or_optimization':False,'results':all_summaries})
 save('audit.json',audits);save('evaluation.json',evaluations)
 save('forward_status.json',{'protocol_commit':PROTOCOL_COMMIT,'forward_earliest_date':'2026-11-05','admitted_data_end':str(d.sessions[-1]),'admitted_forward_sessions':sum(day>=date(2026,11,5) for day in d.sessions),'forward_returns_computed':False,'status':'pending_future_observations','note':'No future prices fabricated. This run is retrospective; protocol does not create a background scheduler.'})
 print('Completed',len(all_summaries),'predeclared scenarios and',len(evaluations),'chronological evaluations;',len(d.sessions),'verified sessions')
if __name__=='__main__':main()
