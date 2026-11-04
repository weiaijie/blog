from pathlib import Path
import urllib.request,urllib.error,json,hashlib,datetime,concurrent.futures
P=Path(__file__).parent
JOBS=[('sse_etf_faq','https://www.sse.com.cn/assortment/fund/etf/question/'),('sse_bond_etf_guide','https://etf.sse.com.cn/ruleguide/guide/c/5287915.shtml'),('sse_fees_2025','https://www.sse.com.cn/services/tradingservice/charge/ssecharge/c/c_20250102_10767593.shtml'),('sse_fees_current','https://www.sse.com.cn/services/tradingservice/charge/ssecharge/'),('csrc_etf_overview','https://www.csrc.gov.cn/qinghai/c105501/c7422297/content.shtml')]
def get(job):
 name,url=job;r={'name':name,'url':url,'requested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as f:b=f.read();r.update(status=f.status,content_type=f.headers.get('Content-Type'))
 except urllib.error.HTTPError as e:b=e.read();r.update(status=e.code,error=str(e))
 except Exception as e:b=b'';r['error']=str(e)
 (P/(name+'.body')).write_bytes(b);r.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return r
if __name__=='__main__':
 if (P/'requests.json').exists():raise SystemExit('Use a fresh snapshot folder; do not overwrite.')
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:r=list(ex.map(get,JOBS))
 (P/'requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print([(x['name'],x.get('status'),x.get('error')) for x in r])
