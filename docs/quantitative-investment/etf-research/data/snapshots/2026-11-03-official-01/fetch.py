from pathlib import Path
import urllib.request,urllib.error,json,hashlib,datetime,concurrent.futures,subprocess
P=Path(__file__).parent
jobs=[('510300_20260112','https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-01-12/510300_20260112_VTCZ.pdf'),('510300_20250611','https://www.sse.com.cn/disclosure/fund/announcement/c/new/2025-06-11/510300_20250611_ZAU4.pdf'),('511010_20260320','https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-03-20/511010_20260320_Y87H.pdf'),('511010_20260622','https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-06-22/511010_20260622_0EYP.pdf'),('511010_20251223','https://www.sse.com.cn/disclosure/fund/announcement/c/new/2025-12-23/511010_20251223_0M89.pdf'),('511010_20250918','https://www.sse.com.cn/disclosure/fund/announcement/c/new/2025-09-18/511010_20250918_FU3S.pdf'),('511010_2013_report','https://static.cninfo.com.cn/finalpage/2014-03-31/63762335.PDF'),('510300_2015_prospectus','https://pdf.dfcfw.com/pdf/H2_AN201512160012117564_1.pdf')]
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
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(fetch,jobs))
 (P/'requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
 print(json.dumps(r,ensure_ascii=False,indent=2))
