from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys
from etf_research.http_capture import fetch,load_policy,save_transport,HOSTS
from etf_research.publication import seal,create
from recent_market_data import SNAPS,MARKET,REGISTER,NOTICES
out=Path(sys.argv[1])
out.mkdir()
(out/'collector.py').write_bytes(Path(__file__).read_bytes())
p=load_policy()
save_transport(out,p)
HOSTS.update(['fundf10.eastmoney.com','static.cninfo.com.cn'])
jobs={}
for folder in (MARKET,REGISTER,NOTICES):
    for r in json.loads((SNAPS/folder/'requests.json').read_bytes()):
        n=r['name']
        if n.startswith(('register_','distribution_','official_','sina_','sohu_','catalog_')):
            jobs[n]=r['url'].replace('2026-10-26','2026-11-24').replace('2026-11-12','2026-11-26').replace('20261112','20261126').replace('20261026','20261102')
        if n=='cninfo_159920':
            url=r['url']
            post=r['post'].replace('2026-10-26','2026-11-24').replace('2026-11-12','2026-11-26')
def batch(jobs):
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(lambda n:fetch(out,n,jobs[n],p),jobs))
rows=batch(jobs)
name='cninfo_159920'
ts=datetime.now(timezone.utc).isoformat()
r=subprocess.run(['curl','--disable','--ipv4','--noproxy','*','--max-time','30','-sS','--referer','https://www.cninfo.com.cn/','-A','Mozilla/5.0','--data',post,'-o',str(out/(name+'.body')),'-w','%{http_code}',url],capture_output=True)
body=(out/(name+'.body')).read_bytes()
rows.append(dict(name=name,url=url,post=post,requested_at_utc=ts,status=int(r.stdout or 0),curl_exit=r.returncode,final_url=url,sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),error=r.stderr.decode()))
pdf={}
for code,n in [('513500','catalog_513500'),('159920',name)]:
    try:
        payload=json.loads((out/(n+'.body')).read_bytes())
        items=payload['result'] if code=='513500' else (payload['announcements'] or [])
        for i,row in enumerate(items):
            u=('https://www.sse.com.cn'+row['URL']) if code=='513500' else ('https://static.cninfo.com.cn/'+row['adjunctUrl'])
            pdf[f'notice_{code}_{i:02}']=u
            print(code,i,row.get('TITLE',row.get('announcementTitle')))
    except (ValueError,KeyError,TypeError) as e:
        print(n,'catalog error',e)
rows+=batch(pdf)
create(out/'requests.json',rows)
seal(out)
print([(r['name'],r['status']) for r in rows])
