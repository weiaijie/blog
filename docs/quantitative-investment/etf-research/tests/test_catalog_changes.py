import unittest,copy,json
from pathlib import Path
from etf_research.catalog_changes import diff_catalogs,risk_hints,official_notice_url,CatalogChanged
from etf_research.admission import check_catalog,catalog_rows
from etf_research.notice_review import prepare_review
ROOT=Path(__file__).resolve().parents[1]/'data/snapshots'
class CatalogChangeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.payload=json.loads((ROOT/'2026-11-03-official-02/510300_all_index.body').read_text());cls.rows=catalog_rows(cls.payload,'510300')
 def test_identical_catalog_empty_and_real_packet_unapproved(self):
  self.assertEqual(diff_catalogs(self.rows,self.rows),[])
  packet=prepare_review(ROOT,'2026-11-05-rules-10');self.assertEqual(packet['changes'],[]);self.assertFalse(packet['approves_prices_or_events'])
 def test_real_historical_dividend_addition_is_pending(self):
  # Synthetic catalog omission of a REAL archived notice; not a newly discovered event.
  target=next(u for u,r in self.rows.items() if '2026' in r['SSEDATE'] and '分红' in r['TITLE'])
  old={k:v for k,v in self.rows.items() if k!=target};d=diff_catalogs(self.rows,old)
  self.assertEqual(len(d),1);self.assertEqual(d[0]['kind'],'added');self.assertIn('cash_distribution',d[0]['risk_hints']);self.assertFalse(d[0]['automatically_admissible'])
 def test_removed_notice_never_cancels_event(self):
  url=next(iter(self.rows));cur={k:v for k,v in self.rows.items() if k!=url};d=diff_catalogs(cur,self.rows)
  self.assertEqual(d[0]['kind'],'removed');self.assertIsNone(d[0]['after']);self.assertFalse(d[0]['automatically_admissible'])
 def test_date_or_title_change_detected(self):
  cur=copy.deepcopy(self.rows);url=next(iter(cur));cur[url]['SSEDATE']='2026-11-05';d=diff_catalogs(cur,self.rows);self.assertEqual(d[0]['kind'],'modified')
  one=d[0]['change_id'];cur[url]['TITLE']+='更正';self.assertNotEqual(diff_catalogs(cur,self.rows)[0]['change_id'],one)
 def test_admission_error_exposes_details_but_still_blocks(self):
  cur=copy.deepcopy(self.payload);cur['result'][0]['TITLE']+='更正';cur['pageHelp']['data']=cur['result']
  with self.assertRaises(CatalogChanged) as ctx:check_catalog(cur,self.payload,'510300')
  self.assertEqual(len(ctx.exception.changes),1);self.assertIn('catalog changed',str(ctx.exception))
 def test_classification_is_advisory_and_ambiguous_is_pending(self):
  self.assertIn('share_change',risk_hints('基金份额折算公告'));self.assertIn('trading_or_fund_status',risk_hints('暂停交易公告'));self.assertEqual(risk_hints('更新资料'),['unclassified_requires_full_text'])
 def test_official_url_restricts_origin_and_path(self):
  self.assertEqual(official_notice_url('/disclosure/fund/announcement/a.pdf'),'https://www.sse.com.cn/disclosure/fund/announcement/a.pdf')
  for value in ['https://evil.example/a.pdf','//evil.example/a.pdf','/disclosure/fund/announcement/../../a.pdf','/other/a.pdf']:
   with self.assertRaises(ValueError):official_notice_url(value)
 def test_diff_order_and_fingerprint_deterministic(self):
  old=dict(list(self.rows.items())[2:]);a=diff_catalogs(self.rows,old);b=diff_catalogs(dict(reversed(list(self.rows.items()))),old);self.assertEqual(a,b)
