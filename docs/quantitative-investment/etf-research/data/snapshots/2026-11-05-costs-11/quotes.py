from fetch import run,BASE
from urllib.parse import urlencode
import concurrent.futures,json
# Probe path composed from the site's published sh1 path, dayk/snap calls and HTTPS host.
# A successful response is still a candidate; no research or forward admission is performed.
jobs=[]
for s in ['510300','511010']:
 jobs.append(('official_dayk_'+s,'https://yunhq.sse.com.cn:32042/v1/sh1/dayk/'+s+'?'+urlencode({'begin':-1000,'end':-1,'period':'day'})))
 jobs.append(('official_snap_'+s,'https://yunhq.sse.com.cn:32042/v1/sh1/snap/'+s+'?'+urlencode({'select':'name,prev_close,open,high,low,last,up_limit,down_limit,tradephase,hlt_tag'})))
params={'isPagination':'true','sqlId':'SSE_PL_JYTS_TFPXX_JJ','secCode':'513100','stopReason':'','order':'startStopDate|desc,secCode|asc','startDate':'20220101','endDate':'20261104','pageHelp.pageSize':25,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.cacheSize':1,'pageHelp.endPage':1}
jobs.append(('suspensions_positive_code','https://query.sse.com.cn/sseQuery/commonSoaQuery.do?'+urlencode(params)))
assert not (BASE/'quote_requests.json').exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(run,jobs))
(BASE/'quote_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
