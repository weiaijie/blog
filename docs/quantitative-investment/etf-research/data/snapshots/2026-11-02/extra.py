import probe,json,concurrent.futures
jobs=[]
for c in ['510300','511010']:
 for adj in ['', 'hfq']:
  jobs.append((f'tencent_{adj or "raw"}_{c}',f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh{c},day,2024-01-01,2026-11-02,640,{adj}'))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(probe.run,jobs))
(probe.BASE/'extra_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for x in r: print(x['name'],x.get('status'),x.get('error'),x['bytes'])
