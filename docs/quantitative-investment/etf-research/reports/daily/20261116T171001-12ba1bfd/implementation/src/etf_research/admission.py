"""Fail-closed incremental raw-price admission; new event notices require review.

No network access and no synthetic price filling. A prior verified dataset is
extended only by complete exchange sessions common to both raw-price providers.
"""
from dataclasses import replace
from datetime import date,datetime,time,timedelta
from decimal import Decimal as D
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from zoneinfo import ZoneInfo
import hashlib,json,re
from .data import load_dataset,verify_manifest,RawBar,SYMBOLS
from .catalog_changes import diff_catalogs,CatalogChanged
TZ=ZoneInfo('Asia/Shanghai')

def completed_date(timestamp):
 if timestamp.tzinfo is None:raise ValueError('Timezone-aware timestamp required')
 t=timestamp.astimezone(TZ)
 return t.date() if t.time()>=time(16) else t.date()-timedelta(days=1)

def sessions_between(ranges,start,end):
 days=[];d=start
 while d<=end:
  if str(d.year) not in ranges:raise ValueError('Calendar year lacks independent evidence')
  closed=any(date.fromisoformat(f'{d.year}-{a}')<=d<=date.fromisoformat(f'{d.year}-{b}') for a,b in ranges[str(d.year)])
  if d.weekday()<5 and not closed:days.append(d)
  d+=timedelta(days=1)
 return tuple(days)

def catalog_rows(payload,symbol):
 rows=payload['result'];page=payload['pageHelp']
 if not rows or page['pageCount']!=1 or page['pageNo']!=1 or page['total']!=len(rows):raise ValueError('Incomplete official catalog pagination')
 if page['data']!=rows:raise ValueError('Official catalog page/result conflict')
 records={}
 for r in rows:
  if r['SECURITY_CODE']!=symbol or r['URL'] in records:raise ValueError('Wrong instrument or duplicate official notice')
  records[r['URL']]={k:r[k] for k in ['TITLE','SSEDATE','SECURITY_CODE']}
 return records

def check_catalog(current,previous,symbol):
 current=catalog_rows(current,symbol);previous=catalog_rows(previous,symbol)
 if current!=previous:raise CatalogChanged(diff_catalogs(current,previous))
 return len(current)

def parse_prices(body,provider,through):
 if provider=='sina':
  s=body.decode('utf-8');rows=json.loads(s[s.index('([')+1:s.rindex(')')]);days=[r['day'] for r in rows]
  fields=[(r['day'],r['open'],r['high'],r['low'],r['close']) for r in rows]
 elif provider=='sohu':
  payload=json.loads(body.decode('gb18030'))
  if len(payload)!=1 or payload[0]['status']!=0:raise ValueError('Failed Sohu data response')
  rows=payload[0]['hq'];days=[r[0] for r in rows];fields=[(r[0],r[1],r[6],r[5],r[2]) for r in rows]
 else:raise ValueError('Unknown raw provider')
 expected=sorted(set(days),reverse=provider=='sohu')
 if not days or days!=expected:raise ValueError('Duplicate or unordered source dates')
 out={}
 for day,op,hi,lo,cl in fields:
  day=date.fromisoformat(day)
  if day>through:continue # Intraday/unrequested tails are never admitted.
  v=[D(x) for x in [op,hi,lo,cl]]
  if any(not x.is_finite() or x<=0 or x%D('.001') for x in v):raise ValueError('Invalid raw price/tick')
  op,hi,lo,cl=v
  if not lo<=min(op,cl)<=max(op,cl)<=hi:raise ValueError('Invalid raw OHLC bounds')
  out[day]=RawBar(day,op,hi,lo,cl)
 return out

def load_incremental(root,snapshot,*,now=None):
 root=Path(root);folder=root/snapshot
 if not folder.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe snapshot path')
 verify_manifest(folder);base=load_dataset(root,extended=True)
 cfg=json.loads((folder/'config.json').read_text());through=date.fromisoformat(cfg['through'])
 if cfg['format']!=1 or cfg['calendar_snapshot']!='2026-11-04-calendar-08':raise ValueError('Unsupported admission configuration')
 if through<=base.sessions[-1]:raise ValueError('Incremental horizon must advance the base sample')
 now=now or datetime.now(TZ)
 if through>completed_date(now):raise ValueError('Requested day is not complete in Shanghai')
 requests=[]
 for f in sorted(folder.glob('*requests.json')):requests+=json.loads(f.read_text())
 req={r['name']:r for r in requests}
 if len(req)!=len(requests):raise ValueError('Duplicate request identity')
 def response(name):
  if not re.fullmatch(r'[a-z0-9_]+',name):raise ValueError('Unsafe response name')
  r=req[name];b=(folder/(name+'.body')).read_bytes()
  if r.get('status')!=200 or r.get('error') or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('Failed/mismatched source response')
  capture=datetime.fromisoformat(r['requested_at_utc'])
  if through>completed_date(capture):raise ValueError('Snapshot was collected before requested day completed')
  return b,r
 calendar=json.loads((root/cfg['calendar_snapshot']/'calendar.json').read_text())
 added=sessions_between(calendar['holiday_ranges'],base.sessions[-1]+timedelta(days=1),through)
 if not added or added[-1]!=through:raise ValueError('Requested endpoint must be an exchange session')
 newbars={s:dict(v) for s,v in base.bars.items()};source_checks={};catalog_counts={}
 for symbol in SYMBOLS:
  body,meta=response('catalog_'+symbol)
  url=urlparse(meta['url']);params=parse_qs(url.query)
  if url.scheme!='https' or url.hostname!='query.sse.com.cn' or params.get('sqlId')!=['COMMON_PL_JJXX_JJGG_NEW_L']:raise ValueError('Wrong official catalog endpoint')
  capture=datetime.fromisoformat(meta['requested_at_utc']).astimezone(TZ)
  if params.get('SECURITY_CODE')!=[symbol] or params.get('START_DATE')!=['2012-01-01'] or params.get('END_DATE')!=[str(capture.date())]:raise ValueError('Official catalog scope/date is not current')
  old=json.loads((root/'2026-11-03-official-02'/f'{symbol}_all_index.body').read_text())
  catalog_counts[symbol]=check_catalog(json.loads(body),old,symbol)
  prices={};overlap={}
  for provider in ['sina','sohu']:
   body,meta=response(cfg['prices'][symbol][provider])
   url=urlparse(meta['url']);params=parse_qs(url.query)
   if provider=='sina' and (url.hostname!='quotes.sina.cn' or params.get('symbol')!=['sh'+symbol] or params.get('scale')!=['240']):raise ValueError('Wrong Sina symbol/frequency')
   if provider=='sohu' and (url.hostname!='q.stock.sohu.com' or params.get('code')!=['cn_'+symbol] or params.get('end')!=[through.strftime('%Y%m%d')] or params.get('period')!=['d']):raise ValueError('Wrong Sohu symbol/horizon')
   prices[provider]=parse_prices(body,provider,through)
   common=set(prices[provider])&set(base.sessions)
   if base.sessions[-1] not in common:raise ValueError('Missing unchanged base anchor in new source')
   for day in common:
    if prices[provider][day]!=base.bars[symbol][day]:raise ValueError('Previously admitted price revision')
   overlap[provider]=len(common)
   if set(d for d in prices[provider] if d>base.sessions[-1])!=set(added):raise ValueError('New source has missing/extra exchange dates')
  for day in added:
   if prices['sina'][day]!=prices['sohu'][day]:raise ValueError('New cross-source OHLC mismatch')
   newbars[symbol][day]=prices['sina'][day]
  source_checks[symbol]={'unchanged_overlap_days':overlap,'new_days':len(added),'exact_ohlc_fields':4*len(added)}
 audit={'admitted':True,'snapshot':snapshot,'through':str(through),'added_sessions':[str(d) for d in added],'total_sessions':len(base.sessions)+len(added),'source_checks':source_checks,'official_catalog_counts':catalog_counts,'new_or_changed_notices':0,'new_events_automatically_created':False,'scope_limit':'Catalog equality is not proof of upstream completeness; any notice change requires manual event/suspension review. Current sources are not proven operationally independent.'}
 provenance=dict(base.provenance);provenance.update(end=str(through),session_count=len(base.sessions)+len(added),incremental_admission=audit,incremental_manifest_sha256=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest())
 return replace(base,sessions=base.sessions+added,bars=newbars,provenance=provenance),audit
