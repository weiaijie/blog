"""Strict parser for SSE dayk evidence; does not admit data or alter accounts."""
from datetime import datetime
from decimal import Decimal,InvalidOperation
import json

def parse_dayk(body,symbol):
 payload=json.loads(body,parse_float=Decimal)
 if payload.get('code')!=symbol:raise ValueError('Unexpected official symbol')
 rows=payload.get('kline');begin=payload.get('begin');end=payload.get('end');total=payload.get('total')
 if not isinstance(rows,list) or not rows:raise ValueError('Missing official rows')
 if any(type(n) is not int for n in [begin,end,total]) or not 0<=begin<end<=total or end-begin!=len(rows):raise ValueError('Invalid official range')
 bars={};previous=None
 for row in rows:
  if not isinstance(row,list) or len(row)!=7 or type(row[0]) is not int:raise ValueError('Invalid official row')
  if len(str(row[0]))!=8:raise ValueError('Invalid official date')
  day=datetime.strptime(str(row[0]),'%Y%m%d').date()
  if previous is not None and day<=previous:raise ValueError('Duplicate/nonmonotonic official dates')
  values=[]
  for value in row[1:5]:
   if isinstance(value,bool) or not isinstance(value,(int,Decimal,str)):raise ValueError('Invalid official price type')
   try:v=Decimal(value)
   except InvalidOperation as e:raise ValueError('Invalid official price') from e
   if not v.is_finite() or v<=0:raise ValueError('Invalid official price')
   if v%Decimal('.001'):raise ValueError('Off-tick official price')
   values.append(v)
  o,h,l,c=values
  if not l<=min(o,c)<=max(o,c)<=h:raise ValueError('Invalid official OHLC')
  bars[day]=dict(zip(['open','high','low','close'],values));previous=day
 return bars
