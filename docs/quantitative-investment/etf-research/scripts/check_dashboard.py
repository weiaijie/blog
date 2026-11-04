"""Optional browser acceptance test; requires Playwright and Chromium."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8765/site/index.html');p.add_argument('--output',type=Path,required=True);p.add_argument('--chromium',default='/usr/bin/chromium');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=a.chromium,headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1360,'height':1000});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 response=page.goto(a.url);assert response.status==200
 assert page.locator('#baseline-rows tr').count()==6
 assert page.locator('#chart polyline').count()==6
 assert page.locator('#sensitivity-rows tr').count()==9
 assert page.locator('#fold-rows tr').count()==4
 assert page.locator('#source-rows tr').count()==24
 assert '4.90%' in page.locator('#baseline-rows').inner_text()
 assert '3.56%' in page.locator('#sensitivity-rows').inner_text()
 page.select_option('#cost','high');assert '4.85%' in page.locator('#baseline-rows').inner_text()
 page.select_option('#strategy','bond_hold');assert '0.00%' in page.locator('#sensitivity-rows tr').first.inner_text()
 page.select_option('#cost','base');page.select_option('#strategy','monthly_50_50')
 # Inspect every relative static link, including downloads and failed-response evidence files.
 bad=[]
 for href in page.locator('a[href]').evaluate_all('(nodes)=>nodes.map(n=>n.href)'):
  if '#' in href:continue
  r=page.request.get(href)
  if r.status!=200:bad.append({'url':href,'status':r.status})
 page.screenshot(path=str(a.output/'dashboard-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(a.output/'dashboard-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'Page horizontally overflows mobile viewport'
 assert not errors,errors
 result={'page_errors':errors,'broken_links':bad,'desktop_and_mobile':True,'baseline_rows':6,'sensitivity_rows':9,'fold_rows':4,'source_rows':24,'svg_series':6,'cost_and_strategy_selectors_verified':True}
 (a.output/'browser_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));browser.close()
 if bad:raise AssertionError(bad)
