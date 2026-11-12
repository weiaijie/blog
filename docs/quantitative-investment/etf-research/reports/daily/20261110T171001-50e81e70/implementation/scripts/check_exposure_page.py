"""Read-only browser checks for the dated holdings page."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8768/site/exposure.html');p.add_argument('--output',type=Path,required=True);p.add_argument('--chromium',required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=a.chromium,headless=True);page=b.new_page(viewport={'width':1360,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 assert page.goto(a.url).status==200
 assert page.locator('table').first.locator('tbody tr').count()==18
 body=page.locator('body').inner_text()
 assert 'Beta为空' in body and '当前实际穿透持仓仍未知' in body and '不是预测或损失上限' in body
 for href in page.locator('a[href]').evaluate_all('(n)=>n.map(x=>x.getAttribute("href"))'):
  if not href.startswith('https://'):assert page.request.get(a.url.rsplit('/',1)[0]+'/'+href).status==200,href
 page.screenshot(path=str(a.output/'exposure-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
 page.screenshot(path=str(a.output/'exposure-mobile.png'),full_page=True);assert not errors
 result={'historical_rows':18,'forward_beta_null_label':True,'dated_holdings_unknown_label':True,'stress_not_forecast_label':True,'local_links_ok':True,'mobile_no_page_overflow':True,'page_errors':errors}
 (a.output/'browser_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));b.close()
