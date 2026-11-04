"""Immutable-source probe. Refuse to overwrite any existing response/index."""
import urllib.request,urllib.error,json,datetime,hashlib,concurrent.futures,pathlib,time
BASE=pathlib.Path(__file__).parent
jobs=[]
for code in ['510300','511010']:
 jobs.append((f'sina_daily_{code}',f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol=sh{code}&scale=240&ma=no&datalen=1970'))
 for year in [2022,2023,2024,2025,2026]:
  end=f'{year}-12-31' if year<2026 else '2026-11-03'
  jobs.append((f'tencent_raw_{code}_{year}',f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh{code},day,{year}-01-01,{end},640,'))
 jobs.append((f'eastmoney_raw_{code}',f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.{code}&klt=101&fqt=0&beg=20220101&end=20261103&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'))
jobs += [('sse_reference_spec','https://www.sse.com.cn/services/tradingtech/development/c/10767151/files/781b2418861147de8725b5915f1c571d.pdf'),('sse_bond_guide','https://etf.sse.com.cn/ruleguide/guide/c/5287915.shtml')]
def run(job):
 name,url=job;p=BASE/(name+'.body')
 if p.exists():raise FileExistsError(p)
 r={'name':name,'url':url,'requested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};t=time.monotonic()
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.sse.com.cn/' if 'sse.com.cn' in url else 'https://finance.sina.com.cn/'})
  with urllib.request.urlopen(req,timeout=25) as resp:body=resp.read();r.update(status=resp.status,content_type=resp.headers.get('Content-Type'),final_url=resp.url)
 except urllib.error.HTTPError as e:body=e.read();r.update(status=e.code,error=str(e))
 except Exception as e:body=b'';r.update(error=type(e).__name__+': '+str(e))
 r.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),elapsed_seconds=round(time.monotonic()-t,2));p.write_bytes(body)
 return r
if __name__=='__main__':
 if (BASE/'requests.json').exists():raise FileExistsError('Use a new timestamped snapshot directory')
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:results=list(ex.map(run,jobs))
 (BASE/'requests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 for r in results:print(r['name'],r.get('status'),r.get('error',''),r['bytes'])
