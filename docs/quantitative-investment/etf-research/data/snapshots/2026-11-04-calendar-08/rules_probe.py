import fetch,json,concurrent.futures
jobs=[('sse_rules_2026','https://www.sse.com.cn/lawandrules/sselawsrules2025/trade/universal/c/c_20260424_10816492.shtml'),('sse_investor_questions','https://www.sse.com.cn/services/investors/questions/')]
if (fetch.BASE/'rules_requests.json').exists():raise FileExistsError('Fresh snapshot required')
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:r=list(ex.map(fetch.run,jobs))
(fetch.BASE/'rules_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
