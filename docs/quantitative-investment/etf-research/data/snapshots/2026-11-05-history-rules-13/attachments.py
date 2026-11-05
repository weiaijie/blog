from fetch import run,BASE
import json,concurrent.futures
jobs=[('rules_2018_doc','https://www.sse.com.cn/lawandrules/sselawsrules2025/repeal/rules/c/10784917/files/ab243f7259464115b6522389422784b3.doc'),('rules_2018_doc2','https://www.sse.com.cn/lawandrules/sselawsrules2025/repeal/rules/c/10784917/files/70b36f9242f84deaa456ad74cf8de5d0.doc'),('amendment_2020_jan','https://www.sse.com.cn/lawandrules/sselawsrules/repeal/rules/c/c_20210531_5478094.shtml')]
assert not (BASE/'attachment_requests.json').exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(run,jobs))
(BASE/'attachment_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
