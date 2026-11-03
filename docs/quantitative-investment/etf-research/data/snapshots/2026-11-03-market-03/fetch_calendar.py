from pathlib import Path
import urllib.request,urllib.error,datetime,json,hashlib,re,concurrent.futures
P=Path(__file__).parent
jobs=[(2022,'https://www.sse.com.cn/disclosure/announcement/general/c/c_20211220_5662606.shtml'),(2023,'https://www.sse.com.cn/disclosure/announcement/general/c/c_20221227_5714458.shtml'),(2024,'https://www.sse.com.cn/disclosure/announcement/general/c/c_20231226_5733939.shtml')]
def get(job):
 y,u=job;r={'year':y,'url':u,'requested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(u,timeout=25) as f:b=f.read();r['status']=f.status
 except urllib.error.HTTPError as e:b=e.read();r.update(status=e.code,error=str(e))
 except Exception as e:b=b'';r['error']=str(e)
 (P/f'sse_{y}.body').write_bytes(b);r.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 s=re.sub('<[^>]+>',' ',b.decode('utf-8',errors='replace'));i=s.find('一、休市安排');print(y,s[i:i+1400]);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(get,jobs))
(P/'requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
