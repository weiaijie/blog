from fetch import run,BASE
import json,concurrent.futures
jobs=[('tax_2018_177','https://fgk.chinatax.gov.cn/zcfgk/c102416/c5251984/content.html'),('tax_2018_177_gx','https://guangxi.chinatax.gov.cn/zcwj/zxwj/201901/t20190104_254522.html'),('sse_suspension','https://www.sse.com.cn/disclosure/dealinstruc/suspension/stock/'),('sse_price_trends','https://www.sse.com.cn/market/price/trends/')]
assert not (BASE/'followup_requests.json').exists()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(run,jobs))
(BASE/'followup_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
