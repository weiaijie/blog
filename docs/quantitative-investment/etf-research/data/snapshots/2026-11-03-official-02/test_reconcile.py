"""Regression checks: reject damaged evidence and silently changed cash-flow facts."""
import unittest,tempfile,shutil,subprocess,sys
from pathlib import Path
P=Path(__file__).parent
class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.work=self.root/P.name
  shutil.copytree(P,self.work,ignore=shutil.ignore_patterns('__pycache__'))
  prev=self.root/'2026-11-03-official-01';prev.mkdir()
  shutil.copy2(P.parent/'2026-11-03-official-01/reconciliation.json',prev/'reconciliation.json')
 def tearDown(self):self.tmp.cleanup()
 def run_check(self):return subprocess.run([sys.executable,str(self.work/'reconcile.py')],capture_output=True).returncode
 def test_preserved_evidence_passes(self):self.assertEqual(self.run_check(),0)
 def test_corrupt_pdf_rejected(self):
  p=self.work/'510300_20240111.pdf';p.write_bytes(p.read_bytes()+b'corruption');self.assertNotEqual(self.run_check(),0)
 def test_changed_payment_date_rejected(self):
  p=self.work/'510300_20240111.txt';s=p.read_text();assert '2024 年 1 月 23 日' in s;p.write_text(s.replace('2024 年 1 月 23 日','2024 年 1 月 24 日'));self.assertNotEqual(self.run_check(),0)
 def test_tenfold_dividend_rejected(self):
  p=self.work/'510300_20240111.txt';s=p.read_text();assert '0.6900' in s;p.write_text(s.replace('0.6900','6.9000'));self.assertNotEqual(self.run_check(),0)
if __name__=='__main__':unittest.main()
