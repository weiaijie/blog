"""Evidence-bound general-rule timeline audit; no trading-engine changes."""
from pathlib import Path
from datetime import date
from collections import Counter
import hashlib,json,re
from etf_research.data import verify_manifest
from etf_research.admission import sessions_between
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/snapshots'
NEW='2026-11-05-history-rules-13';OLD='2026-11-05-rules-10'
def main():
 for name in [NEW,OLD,'2026-11-04-calendar-08']:verify_manifest(BASE/name)
 sources=[]
 def anchor(snapshot,filename,needle):
  p=BASE/snapshot/filename;text=p.read_text();matches=[i+1 for i,l in enumerate(text.splitlines()) if needle in l]
  if not matches:raise ValueError('Missing source anchor '+filename+': '+needle)
  obj={'snapshot':snapshot,'file':filename,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'matching_lines':matches,'anchor':needle};sources.append(obj);return len(sources)-1
 a=anchor(NEW,'rules_2018_notice.txt','自2018年8月20日起实施')
 b=anchor(NEW,'amendment_2020_jan.txt','自2020年1月20日起施行')
 anchor(NEW,'amendment_2020_jan.txt','商品期货交易型开放式指数基金')
 anchor(NEW,'rules_2018_notice.txt','暂缓实施的条款')
 for needle in ['3.1.4','3.1.5','债券交易型开放式指数基金','3.4.7','3.4.11','3.4.13','4.1.3','4.3.2','4.3.3']:
  anchor(NEW,'rules_2018_doc.txt',needle)
 anchor(NEW,'rules_2018_notice.txt','基金、债券、债券买断式回购的收盘价')
 anchor(OLD,'sse_rules_2023_attachment_1.txt','基金的收盘价为')
 anchor(OLD,'sse_rules_2026_attachment_2.txt','基金收盘阶段交易方式由连续竞价调整为收盘集合竞价')
 history=(BASE/OLD/'sse_rules_2026_attachment_1.txt').read_text()
 if '2018年8月6日' not in history.replace(' ','') or '2020年1月7日' not in history.replace(' ',''):raise ValueError('Missing revision chain')
 # Later three version dates were separately established from notices and SSE annual history.
 prior=json.loads((BASE/OLD/'rule_versions.json').read_text())['versions']
 timeline=[{'version':'2018','effective_from':'2018-08-20','end_exclusive':'2020-01-20','basis':[a],'fund_close':'last-minute volume-weighted price; no trade uses previous close'}, {'version':'2018_plus_2020_Jan_amendment','effective_from':'2020-01-20','end_exclusive':'2020-03-13','basis':[a,b],'change_scope':'Adds commodity-futures ETF same-day resale; bond ETF already listed','fund_close':'last-minute volume-weighted price; no trade uses previous close'}]
 for v in prior:
  timeline.append({'version':v['version'],'effective_from':v['effective_from'],'end_exclusive':v.get('superseded_from_exclusive'),'prior_evidence_file':OLD+'/rule_versions.json','fund_close':'closing auction with fallback under general rule' if v['version']=='2026' else 'last-minute volume-weighted price; no trade uses previous close'})
 for i,v in enumerate(timeline[:-1]):
  if v['end_exclusive']!=timeline[i+1]['effective_from']:raise ValueError('Timeline gap or overlap')
 ranges=json.loads((BASE/'2026-11-04-calendar-08/calendar.json').read_text())['holiday_ranges'];sessions=sessions_between(ranges,date(2018,9,14),date(2026,10,30));counts=Counter()
 for day in sessions:
  matches=[v for v in timeline if date.fromisoformat(v['effective_from'])<=day and (not v['end_exclusive'] or day<date.fromisoformat(v['end_exclusive']))]
  if len(matches)!=1:raise ValueError('Session lacks one rule version')
  counts[matches[0]['version']]+=1
 for v in timeline:v['sample_sessions']=counts[v['version']]
 requests=[x for f in (BASE/NEW).glob('*requests.json') for x in json.loads(f.read_text())]
 for r in requests:
  if r.get('status')!=200 or r.get('error') or hashlib.sha256((BASE/NEW/(r['name']+'.body')).read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Invalid rule response')
 result={'reviewed_on_shanghai':'2026-11-05','general_rule_versions':timeline,'sample_sessions':len(sessions),'coverage_complete_for_declared_general_versions':sum(counts.values())==1967,'source_anchors':sources,'source_manifests':{n:hashlib.sha256((BASE/n/'manifest.json').read_bytes()).hexdigest() for n in [NEW,OLD,'2026-11-04-calendar-08']},'requests':len(requests),'http_status_counts':dict(Counter(str(r['status']) for r in requests)),'separate_2019_revision_claimed':False,'trading_engine_changed':False,'all_special_rules_or_actual_fills_verified':False,'limitations':['General-version timeline does not prove no other special notices apply','Ex-reference remains a formula with possible issuer adjustments; no complete historical official reference series','Daily OHLC does not reconstruct closing auctions or last-minute volume-weighted calculations','Frozen 9pct buffer is a research assumption, not the formal daily limit','Deferred block-trade provisions are not treated as active ordinary-auction rules']}
 (ROOT/'reports/2026-11-05-rule-timeline/timeline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'sessions':len(sessions),'version_session_counts':counts,'requests':len(requests),'runtime_changed':False},ensure_ascii=False))
if __name__=='__main__':main()
