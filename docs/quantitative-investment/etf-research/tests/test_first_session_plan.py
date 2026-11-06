"""Synthetic future fixtures are never admitted as market observations."""
from pathlib import Path
from dataclasses import replace
from datetime import datetime,date
from zoneinfo import ZoneInfo
import json,unittest,copy
from etf_research.first_session_plan import prepare,check_execution
from etf_research.forward import advance,digest
from etf_research.admission import load_incremental
from test_forward import fixture,now
ROOT=Path(__file__).resolve().parents[1]
RANGES={'2026':[]}
class FirstSessionPlanTests(unittest.TestCase):
 def setup_data(self):
  full=fixture();days=tuple(d for d in full.sessions if d<=date(2026,11,5));prior=replace(full,sessions=days,bars={s:{d:b for d,b in v.items() if d in days} for s,v in full.bars.items()});state=advance(prior,now=now(5));return full,prior,state
 def plan(self):
  full,prior,state=self.setup_data();return full,prepare(prior,state,RANGES,now=now(6,9))
 def test_previous_only_plan_matches_future_simulation(self):
  full,p=self.plan();self.assertTrue(p['created_before_opening_auction']);self.assertFalse(p['price_or_return_for_target_day_used']);self.assertTrue(all(x['actual_fills'] is None for x in p['portfolios'].values()));c=advance(full,now=now(6));self.assertTrue(check_execution(p,c)['target_units_match'])
 def test_later_target_price_changes_do_not_change_targets(self):
  full,p=self.plan();bars={s:dict(v) for s,v in full.bars.items()};day=date(2026,11,6)
  for s in bars:bars[s][day]=replace(bars[s][day],open=bars[s][day].open*2,high=bars[s][day].high*2,low=bars[s][day].low*2,close=bars[s][day].close*2)
  c=advance(replace(full,bars=bars),now=now(6));self.assertTrue(check_execution(p,c)['target_units_match']);self.assertTrue(any(d['reason']=='conservative_9pct_buffer' for x in c['portfolios'].values() for d in x['decisions']))
 def test_current_day_prices_rejected(self):
  full,prior,state=self.setup_data()
  with self.assertRaisesRegex(ValueError,'previous completed'):prepare(full,state,RANGES,now=now(6,9))
 def test_time_and_target_day_guards(self):
  full,prior,state=self.setup_data()
  for moment in [now(6,10),now(9,9),datetime(2026,11,6,9)]:
   with self.assertRaises(ValueError):prepare(prior,state,RANGES,now=moment)
  p=prepare(prior,state,RANGES,now=datetime(2026,11,6,9,15,tzinfo=ZoneInfo('Asia/Shanghai')));self.assertFalse(p['created_before_opening_auction'])
 def test_plan_tamper_and_changed_target_rejected(self):
  full,p=self.plan();c=advance(full,now=now(6));p['portfolios']['bond_hold_base']['target_units']['511010']+=100
  with self.assertRaisesRegex(ValueError,'checksum'):check_execution(p,c)
  p['plan_sha256']=digest({k:v for k,v in p.items() if k!='plan_sha256'})
  with self.assertRaisesRegex(ValueError,'differs'):check_execution(p,c)
 def test_cannot_claim_execution_before_admission(self):
  full,p=self.plan();c=advance(full,now=now(5))
  with self.assertRaisesRegex(ValueError,'not been admitted'):check_execution(p,c)
 def test_saved_real_plan_exactly_replays(self):
  saved=json.loads((ROOT/'reports/2026-11-06-intent/plan.json').read_text());data,_=load_incremental(ROOT/'data/snapshots','2026-11-05-close-12b');state=json.loads((ROOT/'reports/2026-11-05-long-history/forward_checkpoint.json').read_text());ranges=json.loads((ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json').read_text())['holiday_ranges'];self.assertEqual(prepare(data,state,ranges,now=datetime.fromisoformat(saved['created_at_shanghai'])),saved)
