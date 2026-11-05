"""Offline third-source check after admission; never substitutes missing input."""
from pathlib import Path
from datetime import datetime,date
from decimal import Decimal
from urllib.parse import urlparse,parse_qs
import json,hashlib
from etf_research.data import verify_manifest
from etf_research.admission import load_incremental,completed_date
from etf_research.official_history import parse_dayk
ROOT=Path(__file__).resolve().parents[1]
def audit():
 root=ROOT/'data/snapshots';folder=root/'2026-11-05-official-close-12';verify_manifest(folder);data,_=load_incremental(root,'2026-11-05-close-12b');day=date(2026,11,5)
 req={r['name']:r for r in json.loads((folder/'requests.json').read_text())};results={}
 for symbol in ['510300','511010']:
  for kind in ['dayk','snap']:
   r=req['sse_'+kind+'_'+symbol];body=(folder/(r['name']+'.body')).read_bytes();u=urlparse(r['url'])
   if r.get('status')!=200 or r.get('error') or hashlib.sha256(body).hexdigest()!=r['sha256']:raise ValueError('Failed official close source')
   if u.scheme!='https' or u.hostname!='yunhq.sse.com.cn' or u.port!=32042 or u.path!='/v1/sh1/'+kind+'/'+symbol:raise ValueError('Wrong official close endpoint')
   if completed_date(datetime.fromisoformat(r['requested_at_utc']))<day:raise ValueError('Premature close capture')
   if kind=='dayk':
    if parse_qs(u.query)!={'begin':['-64'],'end':['-1'],'period':['day']}:raise ValueError('Wrong dayk fields')
    bars=parse_dayk(body.decode(),symbol)
   else:
    if parse_qs(u.query).get('select')!=['name,prev_close,open,high,low,last,up_limit,down_limit,tradephase,hlt_tag']:raise ValueError('Wrong snap fields')
    snap=json.loads(body,parse_float=Decimal)
  if snap['code']!=symbol or snap['date']!=20261105 or snap['time']<150000 or len(snap['snap'])!=10:raise ValueError('Stale/invalid closing snapshot')
  if day not in bars:raise ValueError('Missing current official close')
  compared=[d for d in bars if d in data.bars[symbol]]
  for d in compared:
   if any(getattr(data.bars[symbol][d],k)!=v for k,v in bars[d].items()):raise ValueError('Official close/previous-bar conflict')
  if any(bars[day][field]!=snap['snap'][i] for field,i in [('open',2),('high',3),('low',4),('close',5)]):raise ValueError('Official snap/dayk conflict')
  results[symbol]={'compared_days':len(compared),'today':{k:str(v) for k,v in bars[day].items()},'source_snapshot_date':snap['date'],'source_snapshot_time':snap['time'],'reported_phase':snap['snap'][8],'prev_close':str(snap['snap'][1]),'up_limit':str(snap['snap'][6]),'down_limit':str(snap['snap'][7]),'ohlc_matches_admitted_sina_and_sohu':True}
 return {'source_manifest_sha256':hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),'symbols':results,'scope':'Third-source check of observed closing quotes; not proof of every intraday fill or historical ex-reference price.'}
if __name__=='__main__':
 result=audit();(ROOT/'reports/2026-11-05-long-history/official_close.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
