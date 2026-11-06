"""Capture immutable official closing quotes, retaining every failed response."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,concurrent.futures,hashlib,json,time,urllib.request,urllib.error

def collect(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    def fetch(job):
        name,url=job;start=time.monotonic();r=dict(name=name,url=url,requested_at_utc=datetime.now(timezone.utc).isoformat())
        try:
            q=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.sse.com.cn/'})
            with urllib.request.urlopen(q,timeout=25) as response:
                body=response.read();r.update(status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'))
        except urllib.error.HTTPError as e:body=e.read();r.update(status=e.code,error=str(e))
        except Exception as e:body=b'';r['error']=type(e).__name__+': '+str(e)
        (folder/(name+'.body')).write_bytes(body)
        r.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),elapsed_seconds=round(time.monotonic()-start,2));return r
    jobs=[]
    for s in ['510300','511010']:
        for kind,query in [('dayk','begin=-64&end=-1&period=day'),('snap','select=name,prev_close,open,high,low,last,up_limit,down_limit,tradephase,hlt_tag')]:
            jobs.append(('sse_'+kind+'_'+s,'https://yunhq.sse.com.cn:32042/v1/sh1/'+kind+'/'+s+'?'+query))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(fetch,jobs))
    (folder/'requests.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (folder/'collector.py').write_bytes(Path(__file__).read_bytes())
    m={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}
    (folder/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(collect(a.output)))
