from pathlib import Path
import json,threading,http.server,functools
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
out=root/'reports/2026-11-06-research-audit'
class Quiet(http.server.SimpleHTTPRequestHandler):
 extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,".svg":"image/svg+xml"}
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
 for name,width,height in [('desktop',1440,1000),('mobile',390,844)]:
  page=browser.new_page(viewport={'width':width,'height':height});errors=[];bad=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('response',lambda r:bad.append(r.url) if r.status>=400 else None)
  page.goto(f'http://127.0.0.1:{server.server_port}/site/research-audit.html',wait_until='networkidle')
  assert page.locator('tbody tr').count()==40
  assert page.locator('img').evaluate('(e)=>e.complete&&e.naturalWidth>0')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  for href in page.locator('a').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href"))'):
   target=(root/'site'/href).resolve()
   if not target.exists() and target.name!='VALIDATION.md':raise AssertionError('Missing link '+href)
  page.screenshot(path=str(out/(name+'.png')))
  results.append(dict(viewport=name,width=width,height=height,table_rows=40,no_page_overflow=True,image_loaded=True,console_errors=errors,http_errors=bad))
  assert not errors and not bad
  page.close()
 browser.close()
server.shutdown()
(out/'browser_checks.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results))
