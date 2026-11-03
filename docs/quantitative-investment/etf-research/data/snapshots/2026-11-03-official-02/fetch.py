from pathlib import Path
import urllib.request,urllib.error,json,hashlib,datetime,concurrent.futures,subprocess
P=Path(__file__).parent
def fetch(job):
 name,url=job; r={'name':name,'url':url,'requested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as f:b=f.read();r['status']=f.status
 except urllib.error.HTTPError as e:b=e.read();r.update(status=e.code,error=str(e))
 except Exception as e:b=b'';r['error']=str(e)
 r.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());(P/(name+'.pdf')).write_bytes(b)
 if b.startswith(b'%PDF'):
  s=subprocess.run(['pdftotext','-layout',str(P/(name+'.pdf')),str(P/(name+'.txt'))],capture_output=True,text=True);r['extract_exit']=s.returncode
 return r
