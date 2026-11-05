"""Admission failures must be detected even when a candidate manifest is re-signed."""
import unittest,json,hashlib,tempfile,shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from etf_research.admission import load_incremental,completed_date,sessions_between,check_catalog
ROOT=Path(__file__).resolve().parents[1]/'data/snapshots';SNAP='2026-11-05-admission-09'
NOW=datetime(2026,11,5,10,tzinfo=ZoneInfo('Asia/Shanghai'))
class AdmissionTests(unittest.TestCase):
 def mutate(self,callback):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);dst=Path(temp.name)/'snapshots';shutil.copytree(ROOT,dst);folder=dst/SNAP;callback(folder)
  # Preserve coherent request/body hashes so tests reach semantic checks.
  for index in folder.glob('*requests.json'):
   rows=json.loads(index.read_text())
   for row in rows:row['sha256']=hashlib.sha256((folder/(row['name']+'.body')).read_bytes()).hexdigest()
   index.write_text(json.dumps(rows))
  manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file() and p.name!='manifest.json'};(folder/'manifest.json').write_text(json.dumps(manifest));return dst
 def change_json(self,folder,name,callback):
  p=folder/name;x=json.loads(p.read_text(encoding='gb18030' if name.startswith('sohu') else 'utf-8'));callback(x);p.write_text(json.dumps(x))
 def test_real_three_sessions_admitted_with_no_forward_return(self):
  d,a=load_incremental(ROOT,SNAP,now=NOW);self.assertEqual(len(d.sessions),1170);self.assertEqual(a['added_sessions'],['2026-11-02','2026-11-03','2026-11-04']);self.assertEqual(len(d.dividends),10)
  self.assertEqual(a['official_catalog_counts'],{'510300':259,'511010':230})
 def test_clock_uses_shanghai_and_requires_aware_time(self):
  self.assertEqual(str(completed_date(datetime(2026,11,5,7,59,tzinfo=ZoneInfo('UTC')))),'2026-11-04')
  self.assertEqual(str(completed_date(datetime(2026,11,5,8,tzinfo=ZoneInfo('UTC')))),'2026-11-05')
  with self.assertRaises(ValueError):completed_date(datetime(2026,11,5))
 def test_later_clock_cannot_turn_morning_snapshot_into_close(self):
  dst=self.mutate(lambda p:self.change_json(p,'config.json',lambda x:x.update(through='2026-11-05')))
  with self.assertRaisesRegex(ValueError,'collected before'):load_incremental(dst,SNAP,now=datetime(2026,11,5,17,tzinfo=ZoneInfo('Asia/Shanghai')))
 def test_missing_new_day_rejected(self):
  def change(p):self.change_json(p,'sohu_510300.body',lambda x:x[0].update(hq=[r for r in x[0]['hq'] if r[0]!='2026-11-03']))
  with self.assertRaisesRegex(ValueError,'missing/extra'):load_incremental(self.mutate(change),SNAP,now=NOW)
 def test_new_price_conflict_rejected(self):
  def change(p):
   def patch(x):
    row=next(r for r in x[0]['hq'] if r[0]=='2026-11-03');row[2]=str(Decimal(row[2])+Decimal('.001'))
   self.change_json(p,'sohu_510300.body',patch)
  with self.assertRaisesRegex(ValueError,'mismatch'):load_incremental(self.mutate(change),SNAP,now=NOW)
 def test_prior_anchor_revision_rejected(self):
  def change(p):
   def patch(x):
    row=next(r for r in x[0]['hq'] if r[0]=='2026-10-30');row[2]=str(Decimal(row[2])+Decimal('.001'))
   self.change_json(p,'sohu_510300.body',patch)
  with self.assertRaisesRegex(ValueError,'revision'):load_incremental(self.mutate(change),SNAP,now=NOW)
 def test_changed_official_notice_requires_review(self):
  def change(p):
   def patch(x):
    x['result'][0]['TITLE']+='（修改）';x['pageHelp']['data']=x['result']
   self.change_json(p,'catalog_510300.body',patch)
  with self.assertRaisesRegex(ValueError,'catalog changed'):load_incremental(self.mutate(change),SNAP,now=NOW)
 def test_incomplete_catalog_rejected(self):
  dst=self.mutate(lambda p:self.change_json(p,'catalog_510300.body',lambda x:x['pageHelp'].update(pageCount=2)))
  with self.assertRaisesRegex(ValueError,'pagination'):load_incremental(dst,SNAP,now=NOW)
 def test_failed_selected_response_rejected(self):
  def change(p):
   def patch(x):next(r for r in x if r['name']=='sina_510300')['status']=503
   self.change_json(p,'requests.json',patch)
  with self.assertRaisesRegex(ValueError,'Failed/mismatched'):load_incremental(self.mutate(change),SNAP,now=NOW)
 def test_wrong_instrument_request_rejected(self):
  def change(p):
   def patch(x):
    row=next(r for r in x if r['name']=='sina_510300');row['url']=row['url'].replace('sh510300','sh511010')
   self.change_json(p,'requests.json',patch)
  with self.assertRaisesRegex(ValueError,'symbol'):load_incremental(self.mutate(change),SNAP,now=NOW)
 def test_nonofficial_catalog_endpoint_rejected(self):
  def change(p):
   def patch(x):
    row=next(r for r in x if r['name']=='catalog_510300');row['url']=row['url'].replace('query.sse.com.cn','example.invalid')
   self.change_json(p,'requests.json',patch)
  with self.assertRaisesRegex(ValueError,'catalog endpoint'):load_incremental(self.mutate(change),SNAP,now=NOW)
