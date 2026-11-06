"""Create a new timestamped intent artifact from yesterday's verified inputs."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,json
from etf_research.admission import load_incremental
from etf_research.first_session_plan import prepare
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
data,_=load_incremental(ROOT/'data/snapshots','2026-11-05-close-12b')
checkpoint=json.loads((ROOT/'reports/2026-11-05-long-history/forward_checkpoint.json').read_text());calendar=json.loads((ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json').read_text())
plan=prepare(data,checkpoint,calendar['holiday_ranges'],now=datetime.now(ZoneInfo('Asia/Shanghai')))
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('x') as f:f.write(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:plan[k] for k in ['created_at_shanghai','target_session','created_before_opening_auction','plan_sha256']},ensure_ascii=False))
