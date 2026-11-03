from pathlib import Path
from decimal import Decimal as D
import json,datetime
P=Path(__file__).parent
S=P.parent/'2026-11-02'
E=P.parent/'2026-11-03-official-02'/'reconciliation.json'
def load_jsonp(path):
 s=path.read_text();return json.loads(s[s.index('([')+1:s.rindex(')')])
holidays={2022:[('01-01','01-03'),('01-31','02-06'),('04-03','04-05'),('04-30','05-04'),('06-03','06-05'),('09-10','09-12'),('10-01','10-07')],2023:[('01-01','01-02'),('01-21','01-27'),('04-05','04-05'),('04-29','05-03'),('06-22','06-24'),('09-29','10-06')],2024:[('01-01','01-01'),('02-09','02-17'),('04-04','04-06'),('05-01','05-05'),('06-10','06-10'),('09-15','09-17'),('10-01','10-07')]}
holidays.update({int(y):v for y,v in json.loads((S/'calendar_2025_to_20261030.json').read_text())['holidays'].items()})
start=datetime.date(2022,8,9);end=datetime.date(2026,10,30);calendar=[];d=start
while d<=end:
 if d.weekday()<5 and not any(f'{d.year}-{a}'<=str(d)<=f'{d.year}-{b}' for a,b in holidays[d.year]):calendar.append(str(d))
 d+=datetime.timedelta(days=1)
(P/'calendar.json').write_text(json.dumps({'start':str(start),'end':str(end),'construction':'Weekdays minus independently transcribed SSE yearly closure ranges; never inferred from price rows.','holiday_ranges':holidays,'dates':calendar},indent=2))
events=json.loads(E.read_text())['dividends'];out={}
for code in ['510300','511010']:
 rows=load_jsonp(S/f'sina_daily_{code}.body');prices={x['day']:x for x in rows};assert len(prices)==len(rows)
 assert set(prices)==set(calendar)
 for r in rows:
  assert D(r['low'])<=min(D(r['open']),D(r['close']))<=max(D(r['open']),D(r['close']))<=D(r['high'])
  assert D(r['volume'])>=0
 raw=json.loads((S/f'tencent_raw_{code}.body').read_text())['data']['sh'+code]['day'];raw={x[0]:x for x in raw if x[0]<=str(end)}
 hfq=json.loads((S/f'tencent_hfq_{code}.body').read_text())['data']['sh'+code]['hfqday']
 qfq=json.loads((S/f'tencent_daily_{code}.body').read_text())['data']['sh'+code]['qfqday']
 dividends=[r for r in events if r['symbol']==code];hf_scale=D('0.37094933') if code=='510300' else D(1)
 residuals={};failures={}
 for mode,records in [('qfq',qfq),('hfq',hfq)]:
  residuals[mode]=D(0);bad=[]
  for r in records:
   day=r[0]
   adjustment=sum((D(e['per_share']) for e in dividends if (day<e['ex_date']<=str(end) if mode=='qfq' else e['ex_date']<=day)),D(0))
   for field,i in [('open',1),('close',2),('high',3),('low',4)]:
    predicted=(D(prices[day][field])-adjustment) if mode=='qfq' else (D(prices[day][field])+adjustment)*hf_scale
    delta=abs(predicted-D(r[i]));residuals[mode]=max(residuals[mode],delta)
    if delta>D('0.0005'):bad.append({'date':day,'field':field,'residual':str(delta)})
  failures[mode]=bad
 volume_residuals={d:D(prices[d]['volume'])-D(r[5])*100 for d,r in raw.items()}
 vol_bad=[d for d,v in volume_residuals.items() if v!=0]
 out[code]={'calendar_expected':len(calendar),'calendar_missing':[],'calendar_extra':[],'duplicate_dates':0,'ohlc_bounds_valid':True,'comparison_rows':len(raw),'adjustment_fields':['open','close','high','low'],'adjustment_max_absolute_residual':{k:str(v) for k,v in residuals.items()},'beyond_half_tick_count':{k:len(v) for k,v in failures.items()},'failure_examples':{k:v[:5] for k,v in failures.items()},'empirical_hfq_scale':str(hf_scale),'volume_sina_equals_tencent_times_100':not vol_bad,'volume_mismatch_count':len(vol_bad),'volume_mismatch_dates':vol_bad[:10],'volume_scaled_residual_min':str(min(volume_residuals.values())),'volume_scaled_residual_max':str(max(volume_residuals.values())),'consistent_with_nearest_integer_hundred_units':all(abs(v)<=50 for v in volume_residuals.values()),'provider_unit_documentation_status':'not_verified','historical_point_in_time_adjustment_status':'not_verified'}
(P/'market_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
