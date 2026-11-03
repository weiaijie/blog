from pathlib import Path
import urllib.request,urllib.parse,urllib.error,json,datetime,hashlib,concurrent.futures
P=Path(__file__).parent
def get(code):
 params={'sqlId':'COMMON_PL_JJXX_JJGG_NEW_L','isPagination':'true','pageHelp.pageSize':100,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.endPage':1,'pageHelp.cacheSize':1,'SECURITY_CODE':code,'TITLE':'分红','START_DATE':'2012-01-01','END_DATE':'2026-11-03'}
 u='https://query.sse.com.cn/commonQuery.do?'+urllib.parse.urlencode(params);r={'url':u,'requested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.sse.com.cn/'}),timeout=30) as f:b=f.read();r['status']=f.status
 except urllib.error.HTTPError as e:b=e.read();r.update(status=e.code,error=str(e))
 except Exception as e:b=b'';r['error']=str(e)
 r.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());(P/(code+'_index.body')).write_bytes(b);(P/(code+'_index_request.json')).write_text(json.dumps(r,indent=2));print(code,r,b[:150])
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(get,['510300','511010']))
