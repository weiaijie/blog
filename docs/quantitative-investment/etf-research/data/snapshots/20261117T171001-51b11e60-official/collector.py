"""Capture immutable official closing quotes, retaining every failed response."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,concurrent.futures,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from etf_research.http_capture import fetch as fetch_public,load_policy,save_transport

def collect(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    policy=load_policy();save_transport(folder,policy)
    def fetch(job):return fetch_public(folder,*job,policy)
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
