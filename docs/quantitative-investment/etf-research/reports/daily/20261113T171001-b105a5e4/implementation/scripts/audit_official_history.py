"""Offline SSE/Sina/calendar evidence audit; no backtest or forward admission."""
from pathlib import Path
from datetime import date,datetime
from decimal import Decimal
from urllib.parse import urlparse,parse_qs
from collections import Counter
import hashlib,json
from etf_research.data import verify_manifest
from etf_research.admission import completed_date
from etf_research.official_history import parse_dayk
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/snapshots';NEW=BASE/'2026-11-05-costs-11'
def main():
 manifests={}
 for name in ['2026-11-05-costs-11','2026-11-04-expansion-07','2026-11-04-calendar-08']:
  verify_manifest(BASE/name);manifests[name]=hashlib.sha256((BASE/name/'manifest.json').read_bytes()).hexdigest()
 requests=[r for f in sorted(NEW.glob('*requests.json')) for r in json.loads(f.read_text())];byname={r['name']:r for r in requests}
 assert len(byname)==len(requests)
 for r in requests:assert hashlib.sha256((NEW/(r['name']+'.body')).read_bytes()).hexdigest()==r['sha256']
 calendar=json.loads((BASE/'2026-11-04-calendar-08/calendar.json').read_text())['dates']
 result={'format':1,'admitted_to_research':False,'forward_state_changed':False,'snapshot_manifest_sha256':manifests,'requests':len(requests),'http_status_counts':dict(Counter(str(r.get('status')) for r in requests)),'symbols':{}}
 for symbol in ['510300','511010']:
  meta=byname['official_full_'+symbol];u=urlparse(meta['url'])
  assert meta['status']==200 and not meta.get('error') and u.scheme=='https' and u.hostname=='yunhq.sse.com.cn' and u.port==32042 and u.path=='/v1/sh1/dayk/'+symbol
  assert parse_qs(u.query)=={'begin':['0'],'end':['-1'],'period':['day']}
  captured=datetime.fromisoformat(meta['requested_at_utc']);assert captured.tzinfo is not None
  cutoff=completed_date(captured)
  official=parse_dayk((NEW/('official_full_'+symbol+'.body')).read_text(),symbol)
  tail=parse_dayk((NEW/('official_dayk_'+symbol+'.body')).read_text(),symbol)
  # Intraday tails from separate requests can differ. Compare only completed sessions.
  assert all(official[d]==bar for d,bar in tail.items() if d<=cutoff)
  text=(BASE/'2026-11-04-expansion-07'/('sina_daily_'+symbol+'.body')).read_text();sina=json.loads(text[text.index('([')+1:text.rindex(')')])
  days=[x['day'] for x in sina];assert days==sorted(set(days));assert date.fromisoformat(days[-1])<=cutoff
  expected=[d for d in calendar if days[0]<=d<=days[-1]];assert days==expected
  actual=[str(d) for d in official if days[0]<=str(d)<=days[-1]];assert actual==expected
  mismatches=[]
  for row in sina:
   for field in ['open','high','low','close']:
    if Decimal(row[field])!=official[date.fromisoformat(row['day'])][field]:mismatches.append({'date':row['day'],'field':field,'sina':row[field],'sse':str(official[date.fromisoformat(row['day'])][field])})
  result['symbols'][symbol]={'official_rows':len(official),'official_first':str(min(official)),'official_last':str(max(official)),'compared_first':days[0],'compared_last':days[-1],'compared_sessions':len(days),'compared_ohlc_fields':len(days)*4,'mismatches':mismatches,'independent_calendar_matches':True,'incomplete_dates_excluded':[str(d) for d in official if d>cutoff],'capture_completed_cutoff':str(cutoff),'official_url':meta['url'],'official_body_sha256':meta['sha256']}
  assert not mismatches
 result['scope']='Price agreement and independent calendar only. No automatic event admission, backtest extension, historical reference-price proof or trade-fill guarantee. Volume/amount unused.'
 out=ROOT/'reports/2026-11-05-evidence/official_history.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
