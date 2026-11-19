"""Collect an immutable update candidate; collection never admits data by itself."""
from pathlib import Path
from datetime import datetime,date,timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
import argparse,hashlib,json,concurrent.futures,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from etf_research.http_capture import fetch as fetch_public,load_policy,save_transport
from etf_research.admission import completed_date,sessions_between
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--through',type=date.fromisoformat);a=p.parse_args()
 now=datetime.now(ZoneInfo('Asia/Shanghai'));cutoff=completed_date(now)
 calendar=json.loads((ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json').read_text())
 candidates=sessions_between(calendar['holiday_ranges'],date(2026,10,31),cutoff)
 if not candidates:raise ValueError('No completed new exchange session')
 through=a.through or candidates[-1]
 if through not in candidates:raise ValueError('Requested end is uncompleted or outside verified calendar')
 a.output.mkdir(parents=True,exist_ok=False) # Never overwrite a frozen snapshot.
 jobs=[]
 for code in ['510300','511010']:
  jobs += [(f'sina_{code}',f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol=sh{code}&scale=240&ma=no&datalen=1970'),(f'sohu_{code}',f'https://q.stock.sohu.com/hisHq?code=cn_{code}&start=20260101&end={through:%Y%m%d}&stat=1&order=D&period=d&rt=json')]
  params={'sqlId':'COMMON_PL_JJXX_JJGG_NEW_L','isPagination':'true','pageHelp.pageSize':1000,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.endPage':1,'pageHelp.cacheSize':1,'SECURITY_CODE':code,'TITLE':'','START_DATE':'2012-01-01','END_DATE':str(now.date())}
  jobs.append((f'catalog_{code}','https://query.sse.com.cn/commonQuery.do?'+urlencode(params)))
 policy=load_policy();save_transport(a.output,policy)
 def fetch(job):return fetch_public(a.output,*job,policy)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:records=list(ex.map(fetch,jobs))
 selected={s:{'sina':'sina_'+s,'sohu':'sohu_'+s} for s in ['510300','511010']}
 for s in selected:
  if next(r for r in records if r['name']=='sohu_'+s).get('status')!=200:
   name='sohu_retry_'+s;records.append(fetch((name,f'https://q.stock.sohu.com/hisHq?code=cn_{s}&start=20240101&end={through:%Y%m%d}&stat=1&order=D&period=d&rt=json')));selected[s]['sohu']=name
 (a.output/'requests.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 (a.output/'config.json').write_text(json.dumps({'format':1,'through':str(through),'calendar_snapshot':'2026-11-04-calendar-08','prices':selected},indent=2)+'\n')
 (a.output/'collector.py').write_bytes(Path(__file__).read_bytes())
 manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(a.output.iterdir()) if f.is_file()}
 (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'candidate_only':True,'through':str(through),'requests':len(records),'actual_requests':sum(r['actual_requests'] for r in records),'statuses':[r.get('status') for r in records],'output':str(a.output)},ensure_ascii=False))
if __name__=='__main__':main()
