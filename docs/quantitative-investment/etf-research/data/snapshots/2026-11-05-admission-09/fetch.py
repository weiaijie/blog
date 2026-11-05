"""Immutable-source probe. Refuse to overwrite any existing response/index."""
import urllib.request,urllib.error,json,datetime,hashlib,concurrent.futures,pathlib,time
BASE=pathlib.Path(__file__).parent
from urllib.parse import urlencode
jobs=[]
for code in ['510300','511010']:
 jobs += [(f'sina_{code}',f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol=sh{code}&scale=240&ma=no&datalen=64'),(f'sohu_{code}',f'https://q.stock.sohu.com/hisHq?code=cn_{code}&start=20261001&end=20261104&stat=1&order=D&period=d&rt=json')]
 params={'sqlId':'COMMON_PL_JJXX_JJGG_NEW_L','isPagination':'true','pageHelp.pageSize':1000,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.endPage':1,'pageHelp.cacheSize':1,'SECURITY_CODE':code,'TITLE':'','START_DATE':'2012-01-01','END_DATE':'2026-11-05'}
 jobs.append((f'catalog_{code}','https://query.sse.com.cn/commonQuery.do?'+urlencode(params)))
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
