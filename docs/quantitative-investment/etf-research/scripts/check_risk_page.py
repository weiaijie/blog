"""Browser acceptance for the generated offline risk page."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8774/site/risk.html');p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1360,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 assert page.goto(a.url).status==200
 assert page.locator('tbody tr').count()==18 and page.locator('svg').count()==1
 assert '样本不足' in page.locator('body').inner_text() and '不改变交易' in page.locator('body').inner_text()
 for href in page.locator('a[href]').evaluate_all('(n)=>n.map(x=>x.href)'):assert page.request.get(href).status==200,href
 page.screenshot(path=str(a.output/'risk-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
 page.screenshot(path=str(a.output/'risk-mobile.png'),full_page=True);assert not errors,errors
 result={'historical_rows':18,'matplotlib_svg':True,'forward_insufficient_window_label':True,'links_ok':True,'mobile_no_page_overflow':True,'page_errors':errors}
 (a.output/'risk_browser_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));b.close()
