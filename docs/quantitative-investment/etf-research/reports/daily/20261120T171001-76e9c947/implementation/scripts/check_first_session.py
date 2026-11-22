"""Compare saved intentions with an independently admitted later checkpoint."""
from pathlib import Path
import argparse,json
from etf_research.first_session_plan import check_execution
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
plan=json.loads((ROOT/'reports/2026-11-06-intent/plan.json').read_text());state=json.loads(a.state.read_text());result=check_execution(plan,state)
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
