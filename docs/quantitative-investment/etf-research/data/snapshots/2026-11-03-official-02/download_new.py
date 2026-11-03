import fetch,json,concurrent.futures
old={'510300_20250611','510300_20260112','511010_20250918','511010_20251223','511010_20260320','511010_20260622'}
jobs=[]
for c in ['510300','511010']:
 for e in json.loads((fetch.P/(c+'_index.body')).read_text())['result']:
  name=c+'_'+e['SSEDATE'].replace('-','')
  if name not in old:jobs.append((name,'https://www.sse.com.cn'+e['URL']))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(fetch.fetch,jobs))
(fetch.P/'requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print([(x['name'],x.get('status'),x.get('error')) for x in r])
