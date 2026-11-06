from pathlib import Path
from datetime import datetime,timezone
import socket,ssl,time,json,hashlib
root=Path('/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research/data/snapshots')
folder=root/'2026-11-06-tls-address-family-1907';folder.mkdir(exist_ok=False)
rows=[]
for family,label in [(socket.AF_INET6,'ipv6'),(socket.AF_INET,'ipv4')]:
 r=dict(address_family=label,requested_at_utc=datetime.now(timezone.utc).isoformat(),hostname='query.sse.com.cn',certificate_validation=True)
 start=time.monotonic();phase='dns'
 try:
  af,kind,proto,_,addr=socket.getaddrinfo(r['hostname'],443,family,socket.SOCK_STREAM)[0];r['remote_address']=addr[0]
  with socket.socket(af,kind,proto) as sock:
   sock.settimeout(5);phase='tcp_connect';sock.connect(addr);r['tcp_seconds']=time.monotonic()-start
   phase='tls_handshake'
   with ssl.create_default_context().wrap_socket(sock,server_hostname=r['hostname']) as tls:r.update(tls_seconds=time.monotonic()-start,tls_version=tls.version(),tls_verified=True)
 except Exception as e:r.update(error_type=type(e).__name__,error=str(e),failed_phase=phase)
 r['elapsed_seconds']=time.monotonic()-start;rows.append(r)
(folder/'probe.json').write_text(json.dumps(rows,indent=2)+'\n')
(folder/'diagnostic.py').write_bytes(Path(__file__).read_bytes())
(folder/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()},indent=2)+'\n')
print(json.dumps(rows,indent=2))
