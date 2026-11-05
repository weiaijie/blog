from fetch import run,BASE
import json,concurrent.futures
jobs=[('official_full_'+s,'https://yunhq.sse.com.cn:32042/v1/sh1/dayk/'+s+'?begin=0&end=-1&period=day') for s in ['510300','511010']]
assert not (BASE/'history_requests.json').exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:r=list(ex.map(run,jobs))
(BASE/'history_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
