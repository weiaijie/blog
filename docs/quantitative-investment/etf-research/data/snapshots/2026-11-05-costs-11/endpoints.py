from fetch import run,BASE
import concurrent.futures,json
jobs=[('sse_trade_js','https://www.sse.com.cn/xhtml/home/2021public/querySearch/search_tradeTip_2021.js'),('sse_price_js','https://www.sse.com.cn/xhtml/home/2021public/querySearch/search_price_2021.js'),('sse_hq_js','https://www.sse.com.cn/xhtml/home/2021public/querySearch/search_HQ_2021.js')]
assert not (BASE/'endpoint_requests.json').exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(run,jobs))
(BASE/'endpoint_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
