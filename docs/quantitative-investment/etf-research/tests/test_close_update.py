"""Official close rejects stale/wrong-day evidence without modifying accounts."""
from datetime import date
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('close_audit',ROOT/'scripts/audit_official_close.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class CloseUpdateTests(unittest.TestCase):
    def test_new_day_matches(self):
        result=module.audit('2026-11-06-official-close-1650','2026-11-06-close-windows-1653',date(2026,11,6))
        self.assertTrue(all(x['source_snapshot_date']==20261106 and x['ohlc_matches_admitted_sina_and_sohu'] for x in result['symbols'].values()))
    def test_stale_official_snapshot_rejected(self):
        with self.assertRaisesRegex(ValueError,'Premature close capture|Stale/invalid'):
            module.audit('2026-11-05-official-close-12','2026-11-06-close-windows-1653',date(2026,11,6))
    def test_wrong_endpoint_day_rejected(self):
        with self.assertRaisesRegex(ValueError,'endpoint differs'):
            module.audit('2026-11-06-official-close-1650','2026-11-06-close-windows-1653',date(2026,11,5))

if __name__=='__main__':unittest.main()
