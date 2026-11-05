from fetch import run,BASE
from urllib.parse import urlencode
import json,concurrent.futures
params={'isPagination':'true','sqlId':'SSE_PL_JYTS_TFPXX_JJ','secCode':'','stopReason':'','order':'startStopDate|desc,secCode|asc','startDate':'20261001','endDate':'20261104','pageHelp.pageSize':25,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.cacheSize':1,'pageHelp.endPage':1}
jobs=[('suspensions_control','https://query.sse.com.cn/sseQuery/commonSoaQuery.do?'+urlencode(params)),('sse_table_config','https://www.sse.com.cn/xhtml/js/common/table_config.js?v=V3.8.1_20260819')]
assert not (BASE/'control_requests.json').exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:r=list(ex.map(run,jobs))
(BASE/'control_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
