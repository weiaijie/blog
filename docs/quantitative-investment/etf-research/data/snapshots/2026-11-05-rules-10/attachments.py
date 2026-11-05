import fetch,json,concurrent.futures
from html.parser import HTMLParser
from urllib.parse import urljoin,urlencode
from pathlib import Path
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   u=dict(attrs).get('href','')
   if u.endswith('.docx') and u not in self.links:self.links.append(u)
jobs=[]
for r in json.loads((fetch.BASE/'requests.json').read_text()):
 if r['name'].startswith('sse_rules_'):
  p=Links();p.feed((fetch.BASE/(r['name']+'.body')).read_text())
  for i,u in enumerate(p.links):jobs.append((r['name']+'_attachment_'+str(i+1),urljoin(r['url'],u)))
for code in ['510300','511010']:
 params={'sqlId':'COMMON_PL_JJXX_JJGG_NEW_L','isPagination':'true','pageHelp.pageSize':1000,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.endPage':1,'pageHelp.cacheSize':1,'SECURITY_CODE':code,'TITLE':'','START_DATE':'2012-01-01','END_DATE':'2026-11-05'}
 jobs.append(('catalog_'+code,'https://query.sse.com.cn/commonQuery.do?'+urlencode(params)))
if (fetch.BASE/'attachment_requests.json').exists():raise FileExistsError('Fresh snapshot required')
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(fetch.run,jobs))
(fetch.BASE/'attachment_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
