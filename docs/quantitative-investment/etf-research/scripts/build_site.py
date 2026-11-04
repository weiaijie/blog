"""Build a dependency-free dashboard from saved result files, never invented series."""
from pathlib import Path
import json,csv,argparse

def main():
 p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1]
 results=json.loads((a.results/'results.json').read_text());sensitivity=json.loads((a.results/'sensitivity.json').read_text());evaluation=json.loads((a.results/'evaluation.json').read_text())
 nav={};dates=None
 for r in results['results']:
  with (a.results/(r['run']+'_daily.csv')).open() as f:rows=list(csv.DictReader(f))
  current=[x['date'] for x in rows]
  if dates is None:dates=current
  if dates!=current:raise ValueError('NAV dates differ across scenarios')
  nav[r['run']]=[float(x['equity'])/float(r['initial_cash'])*100 for x in rows]
 simplified={name:{'folds':ev['folds'],'rolling_min':min(x['annualized_scenario_return'] for x in ev['rolling_252']),'rolling_max':max(x['annualized_scenario_return'] for x in ev['rolling_252']),'rolling_count':len(ev['rolling_252'])} for name,ev in evaluation.items()}
 snap=root/'data/snapshots/2026-11-04-expansion-07';sources=json.loads((snap/'requests.json').read_text())+json.loads((snap/'followup_requests.json').read_text())
 data={'results':results['results'],'sensitivity':sensitivity['results'],'evaluation':simplified,'dates':dates,'nav':nav,'sources':sources}
 payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text((root/'site/template.html').read_text().replace('__PAYLOAD__',payload))
 print('Built dashboard from',len(nav),'saved NAV series and',len(sensitivity['results']),'sensitivity scenarios')
if __name__=='__main__':main()
