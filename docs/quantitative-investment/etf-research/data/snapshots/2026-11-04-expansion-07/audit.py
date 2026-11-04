"""Verify new raw responses against previously admitted raw prices; no tolerance widening."""
from pathlib import Path
from decimal import Decimal as D
import json,re,hashlib
root=Path(__file__).parent;old=root.parent/'2026-11-02'
def sina(path):
 t=path.read_text();rows=json.loads(t[t.index('([')+1:t.rindex(')')]);days=[r['day'] for r in rows]
 if days!=sorted(set(days)):raise ValueError('Duplicate/nonmonotonic raw dates')
 for r in rows:
  v={k:D(r[k]) for k in ['open','high','low','close']}
  if not 0<v['low']<=min(v['open'],v['close'])<=max(v['open'],v['close'])<=v['high']:raise ValueError('Invalid OHLC')
 return {r['day']:r for r in rows}
results={}
for code in ['510300','511010']:
 new=sina(root/f'sina_daily_{code}.body');prior=sina(old/f'sina_daily_{code}.body');common=sorted(set(new)&set(prior));diff=[]
 for day in common:
  for f in ['open','high','low','close']:
   if D(new[day][f])!=D(prior[day][f]):diff.append({'date':day,'field':f,'prior':prior[day][f],'new':new[day][f]})
 legacy=[]
 for match in re.finditer(r'(\d{6}) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) (\d+)',(root/f'tencent_legacy2022_{code}.body').read_text()):
  raw=match.groups();day='20'+raw[0][:2]+'-'+raw[0][2:4]+'-'+raw[0][4:6];legacy.append({'day':day,**dict(zip(['open','close','high','low'],raw[1:5]))})
 if not legacy:raise ValueError('No legacy rows parsed')
 ldiff=[];compared=0
 for row in legacy:
  if row['day'] not in new:continue
  for f in ['open','close','high','low']:
   compared+=1;delta=abs(D(row[f])-D(new[row['day']][f]))
   if delta:ldiff.append({'date':row['day'],'field':f,'legacy':row[f],'sina':new[row['day']][f],'abs_diff':str(delta)})
 results[code]={'sina_rows':len(new),'sina_start':min(new),'sina_end':max(new),'sina_current_day_excluded_from_research':True,'prior_overlap_days':len(common),'prior_snapshot_ohlc_differences':diff,'legacy_rows':len(legacy),'legacy_start':legacy[0]['day'],'legacy_end':legacy[-1]['day'],'legacy_fields_compared':compared,'legacy_different_fields':len(ldiff),'legacy_max_abs_difference':str(max((D(x['abs_diff']) for x in ldiff),default=D(0))),'legacy_difference_examples':ldiff[:10],'additional_admitted_sessions':0}
requests=json.loads((root/'requests.json').read_text())+json.loads((root/'followup_requests.json').read_text())
report={'requests':len(requests),'http_status_counts':{str(status):sum(r.get('status')==status for r in requests) for status in sorted({r.get('status') for r in requests})},'symbols':results,'decision':'Retain frozen 640-session sample. New Sina history lacks complete independent-calendar and exact cross-source validation; legacy Tencent has coarse/different OHLC and ends in 2022. No tolerance widened. Failed official PDF URLs do not verify historical reference prices.','research_data_end':'2026-10-30'}
(root/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir()) if p.is_file() and p.name!='manifest.json'}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
