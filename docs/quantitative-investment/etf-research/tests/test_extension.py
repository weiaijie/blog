import unittest,json
from pathlib import Path
from etf_research.data import load_dataset,verify_manifest
ROOT=Path(__file__).resolve().parents[1]/'data/snapshots'
class ExtensionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load_dataset(ROOT,extended=True)
 def test_extended_shape_and_official_events(self):
  d=self.data;self.assertEqual(len(d.sessions),1167);self.assertEqual(len(d.dividends),10);self.assertEqual(str(d.sessions[0]),'2022-01-04');self.assertEqual(str(d.sessions[-1]),'2026-10-30')
 def test_old_overlap_unchanged(self):
  old=load_dataset(ROOT)
  for s in old.bars:
   for day,bar in old.bars[s].items():self.assertEqual(bar,self.data.bars[s][day])
 def test_calendar_amendments_and_cross_year_closure(self):
  c=json.loads((ROOT/'2026-11-04-calendar-08/calendar.json').read_text());days=c['dates']
  for day in ['2018-12-31','2019-05-02','2019-05-03','2020-01-31']:self.assertNotIn(day,days)
  for day in ['2019-05-06','2020-02-03']:self.assertIn(day,days)
 def test_extended_source_manifests_and_exact_prices(self):
  verify_manifest(ROOT/'2026-11-04-calendar-08');a=json.loads((ROOT/'2026-11-04-calendar-08/audit.json').read_text())
  self.assertTrue(a['candidate_expansion']['prices_and_calendar_passed']);self.assertEqual(a['candidate_expansion']['symbols']['511010']['different_ohlc_fields'],0)
