"""Independent calendar extension from SSE notices; exact OHLC audit only."""
from pathlib import Path
from datetime import date,timedelta
from decimal import Decimal as D
import json,hashlib
root=Path(__file__).parent
prior=json.loads((root.parent/'2026-11-03-market-03/calendar.json').read_text())
# Manually transcribed from the archived annual notices, with explicit superseding amendments.
ranges={
'2018':[['01-01','01-01'],['02-15','02-21'],['04-05','04-07'],['04-29','05-01'],['06-16','06-18'],['09-22','09-24'],['10-01','10-07'],['12-30','12-31']],
'2019':[['01-01','01-01'],['02-04','02-10'],['04-05','04-07'],['05-01','05-04'],['06-07','06-09'],['09-13','09-15'],['10-01','10-07']],
'2020':[['01-01','01-01'],['01-24','02-02'],['04-04','04-06'],['05-01','05-05'],['06-25','06-27'],['10-01','10-08']],
'2021':[['01-01','01-03'],['02-11','02-17'],['04-03','04-05'],['05-01','05-05'],['06-12','06-14'],['09-19','09-21'],['10-01','10-07']],**prior['holiday_ranges']}
# Independent of price rows. Current-day market completion is a separate admission gate.
start=date(2018,1,1);end=date(2026,11,4);dates=[];day=start
while day<=end:
 if day.weekday()<5 and not any(date.fromisoformat(str(day.year)+'-'+a)<=day<=date.fromisoformat(str(day.year)+'-'+b) for a,b in ranges[str(day.year)]):dates.append(str(day))
 day+=timedelta(days=1)
calendar={'start':str(start),'end':str(end),'construction':'Weekdays minus SSE official annual closures and explicit 2019 Labour Day / 2020 Spring Festival amendments; no price-derived sessions','holiday_ranges':ranges,'cross_year_closures':[{'file':'sse2019.body','range':['2018-12-30','2019-01-01']}],'amendments':[{'file':'sse2019_adjust.body','excluded_additional_weekdays':['2019-05-02','2019-05-03']},{'file':'sse2020_adjust.body','excluded_additional_weekdays':['2020-01-31']}],'new_sources':{year:'sse'+year+'.body' for year in ['2018','2019','2020','2021']},'prior_sources_manifest':'../2026-11-03-market-03/manifest.json','dates':dates,'scope_limit':'Exchange sessions, not per-instrument suspension verification'}
(root/'calendar.json').write_text(json.dumps(calendar,ensure_ascii=False,indent=2)+'\n')
checks={}
def sina(code):
 s=(root.parent/'2026-11-04-expansion-07'/f'sina_daily_{code}.body').read_text();return json.loads(s[s.index('([')+1:s.rindex(')')])
for code in ['510300','511010']:
 rows=sina(code);actual=[r['day'] for r in rows];expected=[d for d in dates if actual[0]<=d<=actual[-1]]
 checks[code]={'sina_rows':len(rows),'independent_expected_sessions':len(expected),'missing_exchange_sessions':sorted(set(expected)-set(actual)),'unexpected_dates':sorted(set(actual)-set(expected)),'duplicate_dates':len(actual)-len(set(actual))}
sohu=json.loads((root/'sohu_510300.body').read_text(encoding='gb18030'))
assert len(sohu)==1 and sohu[0]['status']==0
rows=sohu[0]['hq'];days=[r[0] for r in rows];assert days==sorted(set(days),reverse=True)
sin={r['day']:r for r in sina('510300')};diff=[];common=sorted(set(days)&set(sin))
for r in rows:
 if r[0] not in sin:continue
 for f,i in [('open',1),('close',2),('low',5),('high',6)]:
  if D(r[i])!=D(sin[r[0]][f]):diff.append({'date':r[0],'field':f,'sina':sin[r[0]][f],'sohu':r[i]})
expected=[d for d in dates if min(days)<=d<=max(days)]
audit={'calendar_checks':checks,'sohu_510300':{'rows':len(rows),'start':min(days),'end':max(days),'common_sina_days':len(common),'compared_ohlc_fields':4*len(common),'different_fields':len(diff),'difference_examples':diff[:20],'missing_exchange_sessions':sorted(set(expected)-set(days)),'unexpected_dates':sorted(set(days)-set(expected))},'additional_portfolio_sessions_admitted':0,'decision':'Calendar extension is evidence, not automatic data admission. Retain original 640-day portfolio sample until both instruments pass prices and full official-event coverage.'}
bond=[]
for name in ['sohu_511010_2022','sohu_511010_2023','sohu_511010_recent']:
 result=json.loads((root/(name+'.body')).read_text(encoding='gb18030'))
 assert len(result)==1 and result[0]['status']==0
 bond+=result[0]['hq']
assert len({r[0] for r in bond})==len(bond)
start='2022-01-04';end='2026-10-30';expected=[d for d in dates if start<=d<=end]
expanded={}
for code,source_rows in [('510300',rows),('511010',bond)]:
 raw={r[0]:r for r in source_rows if start<=r[0]<=end};sn={r['day']:r for r in sina(code)};diffs=[]
 for day,r in raw.items():
  for f,i in [('open',1),('close',2),('low',5),('high',6)]:
   if D(r[i])!=D(sn[day][f]):diffs.append({'date':day,'field':f,'sina':sn[day][f],'sohu':r[i]})
 expanded[code]={'rows':len(raw),'expected_sessions':len(expected),'missing_dates':sorted(set(expected)-set(raw)),'extra_dates':sorted(set(raw)-set(expected)),'different_ohlc_fields':len(diffs),'examples':diffs[:10]}
audit['candidate_expansion']={'start':start,'end':end,'symbols':expanded,'prices_and_calendar_passed':all(not x['missing_dates'] and not x['extra_dates'] and x['different_ohlc_fields']==0 for x in expanded.values())}
audit['decision']='Whole 2018 history rejected; 2022 onward candidate must additionally pass official-event loader before portfolio admission.'
(root/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(audit,ensure_ascii=False,indent=2))
