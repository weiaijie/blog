from fetch import run,BASE
from urllib.parse import urlencode
import concurrent.futures,json
jobs=[]
for code in ['510300','511010']:
 params={'isPagination':'true','sqlId':'SSE_PL_JYTS_TFPXX_JJ','secCode':code,'stopReason':'','order':'startStopDate|desc,secCode|asc','startDate':'20220101','endDate':'20261104','pageHelp.pageSize':1000,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.cacheSize':1,'pageHelp.endPage':1}
 jobs.append(('suspensions_'+code,'https://query.sse.com.cn/sseQuery/commonSoaQuery.do?'+urlencode(params)))
jobs.append(('sse_full_js','https://www.sse.com.cn/xhtml/js/sse_full.js?v=3.8.3_20261030'))
assert not (BASE/'suspension_requests.json').exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(run,jobs))
(BASE/'suspension_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
