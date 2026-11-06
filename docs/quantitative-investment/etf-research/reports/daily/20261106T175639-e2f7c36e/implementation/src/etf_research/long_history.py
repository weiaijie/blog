"""Separately admitted 2018-start retrospective sample; frozen loaders unchanged."""
from pathlib import Path
from datetime import date,datetime
from decimal import Decimal as D
from urllib.parse import urlparse,parse_qs
import hashlib,json,re
from .data import Dataset,RawBar,SYMBOLS,verify_manifest
from .accounting import Dividend
from .official_history import parse_dayk
from .admission import parse_prices,catalog_rows,completed_date,sessions_between
START=date(2018,9,14);END=date(2026,10,30)
NAMES=('2026-11-03-official-01','2026-11-03-official-02','2026-11-04-expansion-07','2026-11-04-calendar-08','2026-11-05-costs-11','2026-11-05-events-12')

def checked_events(root,start,end):
 rows=json.loads((root/'2026-11-03-official-02/reconciliation.json').read_text())['dividends'];events=[];sources=[]
 for s in SYMBOLS:
  records=catalog_rows(json.loads((root/'2026-11-03-official-02'/(s+'_all_index.body')).read_text()),s)
  found={'https://www.sse.com.cn'+url for url,item in records.items() if any(w in item['TITLE'] for w in ['分红','收益分配'])}
  known={e['official_evidence']['source_url'] for e in rows if e['symbol']==s}
  if found!=known:raise ValueError('Dividend catalog coverage changed')
  # Complete catalog title search is a bounded check, not an absolute completeness claim.
  if any(item['SSEDATE']>=str(start) for item in records.values() if any(w in item['TITLE'] for w in ['折算','拆分','合并'])):raise ValueError('Unreviewed share-change notice')
 for row in rows:
  record=date.fromisoformat(row['record_date']);pay=date.fromisoformat(row['pay_date'])
  if record<start<=pay:raise ValueError('Initial entitlement requires explicit review')
  if not start<=record<=end:continue
  e=row['official_evidence'];pdf=root/e['snapshot']/e['source_file']
  if not pdf.resolve().is_relative_to(root.resolve()) or hashlib.sha256(pdf.read_bytes()).hexdigest()!=e['pdf_sha256']:raise ValueError('Dividend PDF hash mismatch')
  text=pdf.with_suffix('.txt').read_text()
  parsed={}
  for field,label in [('record_date','权益登记日'),('ex_date','除息日'),('pay_date','现金红利发放日'),('announcement_date',r'公告送出日期\s*[：:]')]:
   m=re.search(label+r'\s*(\d{4})\s*年\s*(\d+)\s*月\s*(\d+)\s*日',text)
   if not m:raise ValueError('Unparsed dividend date '+field)
   parsed[field]=date(*map(int,m.groups()))
  m=re.search(r'本次分红方案[（(]单位[：:]元/10\s*份基金份额[）)]\s*([\d.]+)',text)
  if not m:raise ValueError('Unparsed dividend amount')
  amount=D(m[1])/10
  if row['official_status']!='verified' or amount<=0 or amount!=D(row['per_share']) or amount!=D(e['per_share']):raise ValueError('Dividend amount/evidence conflict')
  if any(str(parsed[k])!=row[k] or row[k]!=e[k] for k in ['record_date','ex_date','pay_date']):raise ValueError('Dividend date/evidence conflict')
  events.append(Dividend(row['symbol'],parsed['announcement_date'],parsed['record_date'],parsed['ex_date'],parsed['pay_date'],amount))
  sources.append({'symbol':row['symbol'],'ex_date':row['ex_date'],'announcement_date':str(parsed['announcement_date']),'pdf':str(pdf.relative_to(root)),'sha256':e['pdf_sha256'],'url':e['source_url']})
 if len({e.key for e in events})!=len(events):raise ValueError('Duplicate dividend')
 return tuple(sorted(events,key=lambda e:(e.ex_date,e.symbol))),sources

def load_long_history(root):
 root=Path(root);manifests={n:verify_manifest(root/n) for n in NAMES}
 calendar=json.loads((root/'2026-11-04-calendar-08/calendar.json').read_text());sessions=sessions_between(calendar['holiday_ranges'],START,END)
 listed=tuple(date.fromisoformat(d) for d in calendar['dates'] if str(START)<=d<=str(END))
 if sessions!=listed:raise ValueError('Independent calendar conflict')
 official=root/'2026-11-05-costs-11';requests={r['name']:r for r in json.loads((official/'history_requests.json').read_text())};bars={}
 for s in SYMBOLS:
  body=(official/('official_full_'+s+'.body')).read_bytes();meta=requests['official_full_'+s];url=urlparse(meta['url'])
  if meta.get('status')!=200 or meta.get('error') or hashlib.sha256(body).hexdigest()!=meta['sha256']:raise ValueError('Failed official source')
  if url.scheme!='https' or url.hostname!='yunhq.sse.com.cn' or url.port!=32042 or url.path!='/v1/sh1/dayk/'+s or parse_qs(url.query)!={'begin':['0'],'end':['-1'],'period':['day']}:raise ValueError('Wrong official history endpoint')
  if completed_date(datetime.fromisoformat(meta['requested_at_utc']))<END:raise ValueError('Premature official snapshot')
  values=parse_dayk(body.decode(),s);sina=parse_prices((root/'2026-11-04-expansion-07'/('sina_daily_'+s+'.body')).read_bytes(),'sina',END)
  if tuple(d for d in values if START<=d<=END)!=sessions or tuple(d for d in sina if START<=d<=END)!=sessions:raise ValueError('Long history calendar gap')
  bars[s]={}
  for d in sessions:
   bar=RawBar(d,**values[d])
   if bar!=sina[d]:raise ValueError('Official/Sina price conflict')
   bars[s][d]=bar
 events,sources=checked_events(root,START,END)
 for e in events:
  if any(d not in sessions for d in [e.record_date,e.ex_date,e.pay_date]):raise ValueError('Event outside verified sessions')
 corporate=json.loads((root/'2026-11-05-events-12/corporate_review.json').read_text())
 if corporate['sample_start']!=str(START) or corporate['sample_end']!=str(END) or corporate['initial_shares']!=0 or D(corporate['initial_receivable'])!=0:raise ValueError('Wrong corporate/initial-state review')
 for e in corporate['split_events']:
  if date.fromisoformat(e['effective_date'])>=START or e['applies_to_expanded_sample']:raise ValueError('Unmodeled share conversion')
  p=root/'2026-11-05-events-12'/e['pdf']
  if not p.resolve().is_relative_to((root/'2026-11-05-events-12').resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=e['pdf_sha256']:raise ValueError('Share-conversion evidence mismatch')
 provenance={'manifests_sha256':{n:hashlib.sha256((root/n/'manifest.json').read_bytes()).hexdigest() for n in NAMES},'price_mode':'unadjusted','volume_loaded':False,'event_sources':sources,'start':str(START),'end':str(END),'session_count':len(sessions),'event_count':len(events),'historical_extension':True,'long_history_extension':True,'not_forward_observations':True,'cross_source':'SSE official dayk and Sina daily; exact OHLC','excluded_current_or_unmatched_dates':True,'initial_entitlement_checked':True,'prelisting_splits_not_reapplied':True,'catalog_scope_limit':'Current complete SSE catalogs and dividend/share-change title coverage; no guarantee against upstream omissions.'}
 return Dataset(sessions,bars,events,provenance)
