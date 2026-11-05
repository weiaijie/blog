"""Real immutable evidence plus explicit tamper fixtures; never fake returns."""
from pathlib import Path
from datetime import date,datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
import unittest,tempfile,shutil,json,hashlib
from etf_research.long_history import load_long_history,checked_events
from etf_research.data import load_dataset
from etf_research.admission import load_incremental
from etf_research.forward import advance
ROOT=Path(__file__).resolve().parents[1];SNAP=ROOT/'data/snapshots'
class LongHistoryTests(unittest.TestCase):
 def test_verified_events_and_old_sample_equal(self):
  d=load_long_history(SNAP);old=load_dataset(SNAP,extended=True)
  self.assertEqual((len(d.sessions),len(d.dividends)),(1967,13))
  self.assertTrue(d.provenance['initial_entitlement_checked'])
  for s in old.bars:
   self.assertTrue(all(d.bars[s][day]==old.bars[s][day] for day in old.sessions))
  self.assertEqual(tuple(e for e in d.dividends if e.record_date>=old.sessions[0]),old.dividends)
 def test_initial_entitlement_crossing_refused(self):
  with self.assertRaisesRegex(ValueError,'Initial entitlement'):checked_events(SNAP,date(2019,1,16),date(2026,10,30))
 def mutate(self,folder,name,change):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for p in SNAP.iterdir():
    if not p.is_dir():continue
    if p.name==folder:shutil.copytree(p,root/p.name)
    else:(root/p.name).symlink_to(p,target_is_directory=True)
   f=root/folder/name;change(f)
   m=root/folder/'manifest.json';v=json.loads(m.read_text());v[name]=hashlib.sha256(f.read_bytes()).hexdigest();m.write_text(json.dumps(v))
   with self.assertRaises(ValueError):load_long_history(root)
 def test_price_conflict_even_with_updated_manifest(self):
  def change(p):
   d=json.loads(p.read_text());row=next(x for x in d['kline'] if x[0]==20190115);row[4]=row[1];row[1]=row[2];p.write_text(json.dumps(d))
  self.mutate('2026-11-05-costs-11','official_full_510300.body',change)
 def test_missing_event_rejected_by_catalog(self):
  def change(p):
   d=json.loads(p.read_text());d['dividends']=[x for x in d['dividends'] if x['ex_date']!='2019-01-16'];p.write_text(json.dumps(d))
  self.mutate('2026-11-03-official-02','reconciliation.json',change)
 def test_changed_amount_rejected_by_original_text(self):
  def change(p):
   d=json.loads(p.read_text());x=next(x for x in d['dividends'] if x['ex_date']=='2019-01-16');x['per_share']='0.590';x['official_evidence']['per_share']='0.590';p.write_text(json.dumps(d))
  self.mutate('2026-11-03-official-02','reconciliation.json',change)
 def test_split_cannot_be_reapplied(self):
  def change(p):
   d=json.loads(p.read_text());d['split_events'][0]['applies_to_expanded_sample']=True;p.write_text(json.dumps(d))
  self.mutate('2026-11-05-events-12','corporate_review.json',change)
 def test_independent_calendar_gap_rejected(self):
  def change(p):
   d=json.loads(p.read_text());d['dates'].remove('2019-01-15');p.write_text(json.dumps(d))
  self.mutate('2026-11-04-calendar-08','calendar.json',change)
class FirstObservationTests(unittest.TestCase):
 NOW=datetime(2026,11,5,18,tzinfo=ZoneInfo('Asia/Shanghai'))
 def test_failed_capture_not_admitted(self):
  with self.assertRaisesRegex(ValueError,'Failed/mismatched'):load_incremental(SNAP,'2026-11-05-close-12',now=self.NOW)
 def test_first_real_observation_no_retroactive_trade_and_retry(self):
  data,_=load_incremental(SNAP,'2026-11-05-close-12b',now=self.NOW)
  prior=json.loads((ROOT/'reports/2026-11-05-admission/forward_checkpoint.json').read_text())
  current=advance(data,prior,now=self.NOW)
  self.assertEqual(current['forward_sessions'],1);self.assertEqual(len(current['portfolios']),18)
  for value in current['portfolios'].values():
   self.assertEqual(value['summary']['trades'],0);self.assertEqual(Decimal(value['summary']['ending_equity']),Decimal('100000'));self.assertEqual(value['summary']['total_return'],0)
  self.assertEqual(advance(data,current,now=self.NOW),current)
