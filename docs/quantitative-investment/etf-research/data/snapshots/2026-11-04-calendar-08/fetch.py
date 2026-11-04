"""Immutable-source probe. Refuse to overwrite any existing response/index."""
import urllib.request,urllib.error,json,datetime,hashlib,concurrent.futures,pathlib,time
BASE=pathlib.Path(__file__).parent
jobs=[('sse2018', 'https://www.sse.com.cn/disclosure/announcement/general/c/c_20171222_4438363.shtml'), ('sse2019', 'https://www.sse.com.cn/disclosure/announcement/general/c/c_20181220_4696473.shtml'), ('sse2020', 'https://www.sse.com.cn/disclosure/announcement/general/c/c_20191220_4969627.shtml'), ('sse2021', 'https://www.sse.com.cn/disclosure/announcement/general/c/c_20201224_5286949.shtml'), ('sse2019_adjust', 'https://www.sse.com.cn/disclosure/announcement/general/c/c_20190418_4771364.shtml'), ('sse2020_adjust', 'https://www.sse.com.cn/disclosure/announcement/general/c/c_20200127_4991582.shtml'), ('sohu_510300', 'https://q.stock.sohu.com/hisHq?code=cn_510300&start=20180914&end=20261030&stat=1&order=D&period=d&rt=json'), ('sohu_511010', 'https://q.stock.sohu.com/hisHq?code=cn_511010&start=20180914&end=20261030&stat=1&order=D&period=d&rt=json')]
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
