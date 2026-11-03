import pathlib,json,re,datetime,csv
from decimal import Decimal as D
P=pathlib.Path(__file__).parent
holidays={2025:[('01-01','01-01'),('01-28','02-04'),('04-04','04-06'),('05-01','05-05'),('05-31','06-02'),('10-01','10-08')],2026:[('01-01','01-03'),('02-15','02-23'),('04-04','04-06'),('05-01','05-05'),('06-19','06-21'),('09-25','09-27'),('10-01','10-07')]}
# Transcribed from saved SSE annual notices, independently of price data. No government make-up weekends.
expected=[]
date=datetime.date(2025,1,1)
while date<=datetime.date(2026,10,30):
 if date.weekday()<5 and not any(f'{date.year}-{a}'<=date.isoformat()<=f'{date.year}-{b}' for a,b in holidays[date.year]):expected.append(date.isoformat())
 date+=datetime.timedelta(days=1)
(P/'calendar_2025_to_20261030.json').write_text(json.dumps({'method':'weekdays minus SSE annual-notice closures; no exceptional closure audit yet','holidays':holidays,'sessions':expected},indent=2))
result={}
for c in ['510300','511010']:
 s=(P/f'sina_daily_{c}.body').read_text();sina=json.loads(s[s.index('([')+1:s.rindex(')')]);S={r['day']:r for r in sina}
 T=json.loads((P/f'tencent_raw_{c}.body').read_text())['data']['sh'+c]['day'];T={r[0]:r for r in T if r[0]<='2026-10-30'}
 common=sorted(set(S)&set(T));diff=[]
 for d in common:
  for k,i in [('open',1),('close',2),('high',3),('low',4)]:
   if D(S[d][k])!=D(T[d][i]):diff.append({'date':d,'field':k,'sina':S[d][k],'tencent':T[d][i]})
 h=(P/f'sina_hfq_{c}.body').read_text();hfq=json.JSONDecoder().raw_decode(h[h.index('{'):])[0]['data'];hfq=sorted(hfq,key=lambda r:r['d'])
 increments={hfq[i]['d']:D(hfq[i]['u'])-D(hfq[i-1]['u']) for i in range(1,len(hfq))}
 html=(P/f'eastmoney_dividend_{c}.body').read_text();events=[]
 for row in re.findall(r'<tr.*?</tr>',html,re.S):
  cells=[re.sub('<[^>]+>','',v).strip() for v in re.findall(r'<td[^>]*>(.*?)</td>',row,re.S)]
  if len(cells)==5 and '每10份派现金' in cells[3]:
   amount=D(re.search(r'现金([\d.]+)元',cells[3]).group(1))/10
   events.append({'record_date':cells[1],'ex_date':cells[2],'pay_date':cells[4],'per_share':str(amount),'sina_increment':str(increments.get(cells[2])),'matches':increments.get(cells[2])==amount})
 adj=[]; max_abs=D(0); beyond_rounding=0
 Q=json.loads((P/f'tencent_daily_{c}.body').read_text())['data']['sh'+c]['qfqday']
 for row in Q:
  day=row[0]
  if day not in S:continue
  future=sum((D(e['per_share']) for e in events if e['ex_date']>day),D(0))
  delta=D(S[day]['close'])-future-D(row[2])
  max_abs=max(max_abs,abs(delta))
  beyond_rounding+=int(abs(delta)>D('0.0005'))
  if abs(delta)>D('0.000001'):adj.append({'date':day,'difference':str(delta)})
 observed={d for d in S if '2025-01-01'<=d<='2026-10-30'}
 result[c]={'sina_rows':len(S),'sina_range':[min(S),max(S)],'tencent_raw_common_rows':len(common),'ohlc_mismatch_count':len(diff),'ohlc_mismatches':diff[:20],'dividend_events':events,'all_dividends_match':all(e['matches'] for e in events),'qfq_cash_subtraction_max_abs_difference':str(max_abs),'qfq_cash_subtraction_beyond_half_tick_count':beyond_rounding,'qfq_cash_subtraction_mismatch_count':len(adj),'qfq_mismatches':adj[:20],'calendar_expected':len(expected),'calendar_missing':sorted(set(expected)-observed),'calendar_extra':sorted(observed-set(expected)),'excluded_tencent_date':'2026-11-02: current session, not confirmed final daily bar'}
(P/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for c,r in result.items():print(c,json.dumps({k:v for k,v in r.items() if k not in ['dividend_events','ohlc_mismatches','qfq_mismatches']},ensure_ascii=False))
