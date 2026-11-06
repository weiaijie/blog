from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse
import concurrent.futures,hashlib,json,os,socket,subprocess,urllib.request
root=Path('/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research')
folder=root/'data/snapshots/2026-11-06-network-diagnosis-1904';folder.mkdir(exist_ok=False)
rows=json.loads((root/'data/snapshots/2026-11-06-close-windows-1653/requests.json').read_text())
url=next(r['url'] for r in rows if r['name']=='catalog_510300')
def probe(mode):
 name='catalog_'+mode;body=folder/(name+'.body');headers=folder/(name+'.headers')
 command=['curl','--silent','--show-error','--connect-timeout','8','--max-time','15','--user-agent','Mozilla/5.0','--referer','https://www.sse.com.cn/','--output',str(body),'--dump-header',str(headers),'--write-out','%{json}']
 if mode!='auto':command+=['--ipv4' if mode=='ipv4' else '--ipv6']
 requested=datetime.now(timezone.utc).isoformat();r=subprocess.run(command+[url],capture_output=True,text=True)
 if not body.exists():body.write_bytes(b'')
 if not headers.exists():headers.write_bytes(b'')
 try:metrics=json.loads(r.stdout)
 except ValueError:metrics={}
 fields=['response_code','remote_ip','remote_port','http_version','ssl_verify_result','time_connect','time_appconnect','time_starttransfer','time_total','num_connects']
 return dict(name=name,url=url,requested_at_utc=requested,exit_code=r.returncode,error=r.stderr.strip(),bytes=body.stat().st_size,sha256=hashlib.sha256(body.read_bytes()).hexdigest(),metrics={k:metrics.get(k) for k in fields})
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:results=list(ex.map(probe,['auto','ipv4','ipv6']))
(folder/'requests.json').write_text(json.dumps(results,indent=2)+'\n')
(folder/'diagnostic.py').write_bytes(Path(__file__).read_bytes())
summary=dict(dns_addresses=sorted({x[4][0] for x in socket.getaddrinfo('query.sse.com.cn',443)}),proxy_schemes=sorted(urllib.request.getproxies().keys()))
(folder/'environment.json').write_text(json.dumps(summary,indent=2)+'\n')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(probes=results,environment=summary),indent=2))
