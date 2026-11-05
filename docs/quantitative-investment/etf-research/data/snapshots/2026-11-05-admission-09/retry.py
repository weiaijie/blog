import fetch,json,concurrent.futures
jobs=[('sohu_year_511010','https://q.stock.sohu.com/hisHq?code=cn_511010&start=20260101&end=20261104&stat=1&order=D&period=d&rt=json'),('sohu_recent_511010','https://q.stock.sohu.com/hisHq?code=cn_511010&start=20240101&end=20261104&stat=1&order=D&period=d&rt=json')]
if (fetch.BASE/'retry_requests.json').exists():raise FileExistsError('New directory required')
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:r=list(ex.map(fetch.run,jobs))
(fetch.BASE/'retry_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
