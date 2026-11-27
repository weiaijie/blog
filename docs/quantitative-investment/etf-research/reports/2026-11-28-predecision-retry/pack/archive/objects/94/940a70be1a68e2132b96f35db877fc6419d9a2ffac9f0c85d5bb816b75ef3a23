"""Create an evidence-bound review packet without changing any admission decision."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from datetime import datetime
import hashlib,json
from .data import verify_manifest,SYMBOLS
from .admission import catalog_rows,TZ
from .catalog_changes import diff_catalogs,canonical,official_notice_url

def prepare_review(root,snapshot,baseline='2026-11-03-official-02'):
 root=Path(root);folders={}
 for key,name in [('candidate',snapshot),('baseline',baseline)]:
  folder=root/name
  if not folder.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe snapshot path')
  verify_manifest(folder);folders[key]=folder
 requests=[]
 for p in sorted(folders['candidate'].glob('*requests.json')):requests+=json.loads(p.read_text())
 byname={r['name']:r for r in requests}
 if len(byname)!=len(requests):raise ValueError('Duplicate request identity')
 packet={'format':1,'candidate_snapshot':snapshot,'baseline_snapshot':baseline,'snapshot_manifest_sha256':{key:hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest() for key,p in folders.items()},'symbols':{},'changes':[],'approves_prices_or_events':False}
 for symbol in SYMBOLS:
  name='catalog_'+symbol;meta=byname[name];body=(folders['candidate']/(name+'.body')).read_bytes()
  if meta.get('status')!=200 or meta.get('error') or hashlib.sha256(body).hexdigest()!=meta['sha256']:raise ValueError('Invalid official catalog response')
  parsed=urlparse(meta['url']);q=parse_qs(parsed.query);captured=datetime.fromisoformat(meta['requested_at_utc'])
  if captured.tzinfo is None or parsed.scheme!='https' or parsed.hostname!='query.sse.com.cn' or q.get('sqlId')!=['COMMON_PL_JJXX_JJGG_NEW_L'] or q.get('SECURITY_CODE')!=[symbol] or q.get('START_DATE')!=['2012-01-01'] or q.get('END_DATE')!=[str(captured.astimezone(TZ).date())]:raise ValueError('Unverified official catalog request scope')
  old_body=(folders['baseline']/(symbol+'_all_index.body')).read_bytes()
  current=catalog_rows(json.loads(body),symbol);previous=catalog_rows(json.loads(old_body),symbol);changes=diff_catalogs(current,previous)
  for item in changes:
   item['symbol']=symbol;item['official_url']=official_notice_url(item['url'])
   item['required_checks']=['Read full official text, not title alone','Check publication date and effective dates','Assess cash/share changes and trading restrictions','Preserve earlier events; removal is not automatic cancellation']
  packet['symbols'][symbol]={'current_count':len(current),'baseline_count':len(previous),'candidate_body_sha256':hashlib.sha256(body).hexdigest(),'baseline_body_sha256':hashlib.sha256(old_body).hexdigest(),'captured_at_utc':meta['requested_at_utc'],'changes':len(changes)}
  packet['changes']+=changes
 packet['status']='review_required' if packet['changes'] else 'no_catalog_changes_in_observed_snapshot'
 packet['packet_sha256']=hashlib.sha256(canonical(packet).encode()).hexdigest()
 return packet
