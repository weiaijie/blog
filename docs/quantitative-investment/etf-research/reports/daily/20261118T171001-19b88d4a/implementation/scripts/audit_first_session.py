"""Replay the saved plan using its recorded creation time; never redate it."""
from pathlib import Path
from datetime import datetime
import argparse,json
from etf_research.admission import load_incremental
from etf_research.first_session_plan import prepare
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
saved=json.loads((ROOT/'reports/2026-11-06-intent/plan.json').read_text());data,_=load_incremental(ROOT/'data/snapshots','2026-11-05-close-12b');state=json.loads((ROOT/'reports/2026-11-05-long-history/forward_checkpoint.json').read_text());calendar=json.loads((ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json').read_text())
replayed=prepare(data,state,calendar['holiday_ranges'],now=datetime.fromisoformat(saved['created_at_shanghai']))
if replayed!=saved:raise ValueError('Saved plan does not reproduce')
result={'plan_sha256':saved['plan_sha256'],'creation_timestamp_replayed':saved['created_at_shanghai'],'exact_replay':True,'new_market_data_fetched':False,'no_current_day_prices':True,'account_state_changed':False,'portfolios':len(saved['portfolios'])}
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
