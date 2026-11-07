from datetime import date,timedelta
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_recovery import episodes


class RecoveryTests(unittest.TestCase):
    def test_equal_high_equal_low_and_open_tail(self):
        days=[date(2026,1,1)+timedelta(days=i) for i in range(7)]
        rows=episodes(days,list(map(D,['10','10','8','8','10','9','9.5'])))
        self.assertEqual(len(rows),2)
        self.assertEqual((rows[0]['peak'],rows[0]['trough'],rows[0]['recovery']),(days[1],days[2],days[4]))
        self.assertEqual((rows[0]['peak_to_end'],rows[0]['underwater_closes']),(3,2))
        self.assertEqual((rows[1]['trough_to_recovery'],rows[1]['recovery'],rows[1]['peak_to_end']),(None,None,2))

    def test_flat_portfolio_has_no_episode(self):
        self.assertEqual(episodes([date(2025,1,1),date(2025,1,2)],[D(1),D(1)]),[])
