from pathlib import Path
import json,sys,subprocess,hashlib
from datetime import datetime,timezone
from etf_research.publication import create,seal
p=Path(sys.argv[1])
p.mkdir()
(p/'collector.py').write_bytes(Path(__file__).read_bytes())
r=next(r for r in json.loads((Path(sys.argv[2])/'requests.json').read_bytes()) if r['name']=='cninfo_159920')
q=r['post'].replace('2026-11-24~','2026-10-26~')
ts=datetime.now(timezone.utc).isoformat()
res=subprocess.run(['curl','--disable','--ipv4','--noproxy','*','--max-time','30','-sS','--referer','https://www.cninfo.com.cn/','-A','Mozilla/5.0','--data',q,'-o',str(p/'control.body'),'-w','%{http_code}',r['url']],capture_output=True)
body=(p/'control.body').read_bytes()
create(p/'request.json',dict(url=r['url'],post=q,status=int(res.stdout or 0),curl_exit=res.returncode,sha256=hashlib.sha256(body).hexdigest(),requested_at_utc=ts,error=res.stderr.decode()))
seal(p)
print(json.loads(body)['totalAnnouncement'])
