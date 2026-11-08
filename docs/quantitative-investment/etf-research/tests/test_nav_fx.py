import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from nav_fx_sources import checked
from attribute_nav_fx import stock_parts


def quote(price,nav,fx):
    return dict(close_cny=D(price),nav_cny=D(nav) if nav else None,cny_per_fc=D(fx) if fx else None)


class NavFxTests(unittest.TestCase):
    def test_fx_and_premium_change_independently(self):
        a,b=quote(22,20,2),quote(29,30,3)
        self.assertEqual(stock_parts(100,a,b),{'nav_in_fx_units':0,'fx_translation':1000,'premium_gap':-300})

    def test_missing_nav_or_fx_preserves_observable_pnl(self):
        a=quote(22,20,2)
        self.assertEqual(stock_parts(100,a,quote(21,None,2)),{'stock_without_nav_split':-100})
        self.assertEqual(stock_parts(100,a,quote(21,19,None)),{'nav_without_fx_split':-100,'premium_gap':0})

    def test_conflicting_and_unconfirmed_observations_stay_unknown(self):
        self.assertEqual(checked(D(1),[D(1),D(2)]),(None,'conflict'))
        self.assertEqual(checked(None,[D(1)]),(None,'missing_primary'))
        self.assertEqual(checked(D(1),[None]),(None,'missing_crosscheck'))
