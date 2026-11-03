import probe,json,concurrent.futures,re
jobs=[('sse_2025','https://www.sse.com.cn/disclosure/announcement/general/c/c_20241223_10767108.shtml'),('sse_2026','https://www.sse.com.cn/disclosure/announcement/general/c/c_20251222_10802507.shtml')]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:r=list(ex.map(probe.run,jobs))
(probe.BASE/'calendar_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for x in r:
 print(x['name'],x.get('status'),x.get('error'))
 s=(probe.BASE/(x['name']+'.body')).read_text(errors='replace');s=re.sub('<[^>]+>',' ',s)
 pos=s.find('一、休市');print(s[pos:pos+3200] if pos>=0 else s[-5000:])
