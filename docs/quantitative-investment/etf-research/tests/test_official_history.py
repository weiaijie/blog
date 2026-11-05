"""Explicit synthetic parser fixtures, never market/research inputs."""
import json,unittest
from etf_research.official_history import parse_dayk
class OfficialHistoryTests(unittest.TestCase):
 def fixture(self):return {'code':'510300','begin':0,'end':2,'total':2,'kline':[[20260105,4,4.1,3.9,4.05,1,4],[20260106,4.05,4.2,4,4.15,1,4]]}
 def parse(self,d):return parse_dayk(json.dumps(d),'510300')
 def test_valid_exact_decimal(self):
  from decimal import Decimal
  self.assertEqual(list(self.parse(self.fixture()).values())[0]['close'],Decimal('4.05'))
 def test_wrong_symbol(self):
  d=self.fixture();d['code']='511010'
  with self.assertRaises(ValueError):self.parse(d)
 def test_duplicate_or_reversed_days(self):
  for day in [20260105,20260104]:
   d=self.fixture();d['kline'][1][0]=day
   with self.assertRaises(ValueError):self.parse(d)
 def test_range_and_empty(self):
  for key,value in [('end',3),('begin',-1),('total',1),('kline',[])]:
   d=self.fixture();d[key]=value
   with self.assertRaises(ValueError):self.parse(d)
 def test_invalid_price(self):
  for value in ['NaN','Infinity',0,-1,True,'4.0001']:
   d=self.fixture();d['kline'][0][1]=value
   with self.assertRaises(ValueError):self.parse(d)
 def test_invalid_ohlc(self):
  d=self.fixture();d['kline'][0][3]=4.09
  with self.assertRaises(ValueError):self.parse(d)
 def test_invalid_date(self):
  d=self.fixture();d['kline'][0][0]=20260230
  with self.assertRaises(ValueError):self.parse(d)
