import fetch,json,concurrent.futures
rows=json.loads((fetch.P/'510300_older_index.body').read_text())['result']
jobs=[('510300_'+e['SSEDATE'].replace('-',''),'https://www.sse.com.cn'+e['URL']) for e in rows if '收益分配' in e['TITLE'] or '分红' in e['TITLE']]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(fetch.fetch,jobs))
(fetch.P/'older_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print([(x['name'],x.get('status'),x.get('error'),x.get('extract_exit')) for x in r])
