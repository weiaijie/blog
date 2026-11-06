"""Tampered copies exercise rejection; fixtures never enter market research."""
import copy, hashlib, importlib.util, json, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('suspension_audit',Path(__file__).resolve().parents[1]/'scripts/audit_suspensions.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class SuspensionEvidenceTests(unittest.TestCase):
    def fixture(self,name):
        records=sum((json.loads((a.SNAPSHOT/n).read_text()) for n in ('requests.json','followup_requests.json')),[])
        m=copy.deepcopy(next(r for r in records if r['name']==name));return m,(a.SNAPSHOT/(name+'.body')).read_bytes()
    def test_real_audit(self):
        d=a.audit();self.assertEqual(d['requests'],42);self.assertEqual(d['distinct_full_records'],1340);self.assertFalse(d['absence_proves_no_suspensions'])
    def test_partial_page_not_complete(self):
        m,b=self.fixture('control_2026')
        with self.assertRaisesRegex(ValueError,'Incomplete pagination'):a.validate(m,b)
        self.assertEqual(len(a.validate(m,b,False)[0]),25)
    def test_hash_mismatch(self):
        m,b=self.fixture('full_510300')
        with self.assertRaisesRegex(ValueError,'hash'):a.validate(m,b+b' ')
    def test_failed_response(self):
        m,b=self.fixture('full_510300');m['status']=503
        with self.assertRaisesRegex(ValueError,'Failed'):a.validate(m,b)
    def test_wrong_host(self):
        m,b=self.fixture('full_510300');m['url']=m['url'].replace('query.sse.com.cn','example.com')
        with self.assertRaisesRegex(ValueError,'endpoint'):a.validate(m,b)
    def test_wrong_security(self):
        m,b=self.fixture('overlap_inside');m['url']=m['url'].replace('512300','510300');m['final_url']=m['url']
        with self.assertRaisesRegex(ValueError,'security'):a.validate(m,b)
    def test_outside_interval(self):
        m,b=self.fixture('overlap_inside');m['url']=m['url'].replace('20210101','20190101').replace('20210131','20190131');m['final_url']=m['url']
        with self.assertRaisesRegex(ValueError,'outside'):a.validate(m,b)
    def test_open_end_preserved(self):
        d=a.audit();self.assertTrue(d['open_end_distinct_records']);self.assertTrue(all(r['endStopDate']=='' for r in d['open_end_distinct_records']))
if __name__=='__main__':unittest.main()
