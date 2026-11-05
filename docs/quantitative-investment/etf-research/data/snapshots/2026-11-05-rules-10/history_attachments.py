import fetch,json,concurrent.futures
from html.parser import HTMLParser
from urllib.parse import urljoin
class L(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):
  u=dict(attrs).get('href','')
  if tag=='a' and u.endswith('.docx') and u not in self.urls:self.urls.append(u)
p=L();p.feed((fetch.BASE/'sse_rules_2020.body').read_text())
base=next(r['url'] for r in json.loads((fetch.BASE/'history_requests.json').read_text()) if r['name']=='sse_rules_2020')
jobs=[('sse_rules_2020_attachment_'+str(i+1),urljoin(base,u)) for i,u in enumerate(p.urls)]
jobs.append(('sse_2023_events','https://www.sse.com.cn/aboutus/publication/yearly/documents/c/10764669/files/d712ddc42b2a460483be185fbbb52ea2.pdf'))
if (fetch.BASE/'history_attachment_requests.json').exists():raise FileExistsError('Fresh snapshot required')
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(fetch.run,jobs))
(fetch.BASE/'history_attachment_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
