import urllib.request,urllib.parse,json,hashlib,datetime,pathlib
P=pathlib.Path(__file__).parent
params={'sqlId':'COMMON_PL_JJXX_JJGG_NEW_L','isPagination':'true','pageHelp.pageSize':1000,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.endPage':1,'pageHelp.cacheSize':1,'type':'inParams','SECURITY_CODE':'510300','TITLE':'','START_DATE':'2012-01-01','END_DATE':'2021-12-31','DATE_DESC':1}
u='https://query.sse.com.cn/commonQuery.do?'+urllib.parse.urlencode(params)
r={'url':u,'requested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.sse.com.cn/'}),timeout=30) as f:b=f.read();r['status']=f.status
except Exception as e:b=b'';r['error']=str(e)
(P/'510300_older_index.body').write_bytes(b);r.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());(P/'510300_older_index_request.json').write_text(json.dumps(r,indent=2))
if b:
 d=json.loads(b);print({k:v for k,v in d['pageHelp'].items() if k!='data'});print(json.dumps([e for e in d['result'] if any(w in e['TITLE'] for w in ['分红','分配','收益'])],ensure_ascii=False))
else:print(r)
