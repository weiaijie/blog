from fetch import run,BASE
from urllib.parse import urlencode
import json,concurrent.futures

def url(code,start,end):
 return 'https://query.sse.com.cn/sseQuery/commonSoaQuery.do?'+urlencode({'isPagination':'true','sqlId':'SSE_PL_JYTS_TFPXX_JJ','secCode':code,'stopReason':'','order':'startStopDate|desc,secCode|asc','startDate':start,'endDate':end,'pageHelp.pageSize':1000,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.cacheSize':1,'pageHelp.endPage':1})
jobs=[]
for year in range(2018,2027):jobs.append((f'all_{year}',url('','20180914' if year==2018 else f'{year}0101','20261105' if year==2026 else f'{year}1231')))
for s in ['510300','511010']:jobs.append(('lookback_'+s,url(s,'20120101','20180913')))
jobs += [('overlap_inside',url('512300','20210101','20210131')),('overlap_with_start',url('512300','20201201','20210311'))]
assert not (BASE/'followup_requests.json').exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(run,jobs))
(BASE/'followup_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
