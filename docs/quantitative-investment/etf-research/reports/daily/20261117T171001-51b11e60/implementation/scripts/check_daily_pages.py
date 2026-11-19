"""Desktop/mobile checks against the published active bundle via HTTP."""
from pathlib import Path
import argparse,json
from urllib.parse import urljoin,urlparse
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8768/site/daily.html');p.add_argument('--output',type=Path,required=True);p.add_argument('--chromium',required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=a.chromium,headless=True);page=b.new_page(viewport={'width':1360,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    assert page.goto(a.url).status==200
    page.get_by_role('link',name='打开完整日报').wait_for()
    destination=page.get_by_role('link',name='打开完整日报').get_attribute('href');base=urljoin(a.url,destination)
    checked=0
    for name in ['index','risk','exposure','monthly']:
        url=urljoin(base,name+'.html');assert page.goto(url).status==200
        for href in page.locator('a[href]').evaluate_all('(n)=>n.map(x=>x.href)'):
            if urlparse(href).netloc==urlparse(base).netloc:assert page.request.get(href).status==200,href;checked+=1
        if name=='index':assert '同一期国债合计敞口' in page.locator('body').inner_text()
        if name=='monthly':
            assert page.locator('section').first.locator('tbody tr').count()>=1
            assert page.locator('section').last.locator('tbody tr').count()==98
            assert '部分月' in page.locator('body').inner_text()
        if name=='risk':assert page.locator('tbody tr').count()==18
        if name=='exposure':assert page.locator('table').first.locator('tbody tr').count()==18 and '当前实际穿透持仓仍未知' in page.locator('body').inner_text()
        page.set_viewport_size({'width':1360,'height':1000});page.screenshot(path=str(a.output/(name+'-desktop.png')),full_page=name!='monthly')
        page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),name
        page.screenshot(path=str(a.output/(name+'-mobile.png')),full_page=name!='monthly')
    assert not errors
    result=dict(active_pointer_routed=True,pages=4,local_links_checked=checked,desktop_and_mobile=True,mobile_no_overflow=True,page_errors=errors)
    (a.output/'browser_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));b.close()
