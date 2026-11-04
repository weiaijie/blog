"""Bounded documented/public URL retries; preserve all first failures."""
import fetch,json,concurrent.futures,pathlib,hashlib
jobs=[]
for c in ['510300','511010']:
 jobs.append((f'tencent_prior_url_{c}',f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh{c},day,2024-01-01,2026-11-02,640,'))
 jobs.append((f'tencent_default_{c}',f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh{c},day,,,640,'))
 jobs.append((f'tencent_legacy2022_{c}',f'https://data.gtimg.cn/flashdata/hushen/daily/22/sh{c}.js'))
jobs += [('sse_reference_spec_alt','https://www.sse.com.cn/services/tradingtech/data/c/10762484/files/152e4250c3e2406faa232b75b1da8143.pdf'),('sse_etf_faq','https://www.sse.com.cn/assortment/fund/etf/question/')]
if (fetch.BASE/'followup_requests.json').exists():raise FileExistsError('Use a fresh snapshot directory')
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(fetch.run,jobs))
(fetch.BASE/'followup_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
