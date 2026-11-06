from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build_holdings_audit import extract_stocks,SOURCE


class HoldingsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.text=(SOURCE/'interim_510300.txt').read_text(encoding='utf-8')
    def test_full_stock_tables_and_spaced_name(self):
        rows=extract_stocks(self.text)
        self.assertEqual(len(rows),339)
        self.assertEqual(next(r for r in rows if r['code']=='000725')['fair_value'],'1017211343.96')
    def test_missing_row_blocks(self):
        with self.assertRaisesRegex(ValueError,'ranks'):extract_stocks(self.text.replace('300308','X00308'))
    def test_changed_value_blocks(self):
        with self.assertRaisesRegex(ValueError,'total'):extract_stocks(self.text.replace('4,504,019,440.00','4,504,019,440.01'))
    def test_duplicate_rank_blocks(self):
        with self.assertRaisesRegex(ValueError,'ranks'):extract_stocks(self.text.replace('300    001391','299    001391'))
