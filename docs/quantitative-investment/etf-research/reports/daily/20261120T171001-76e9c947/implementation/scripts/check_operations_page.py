"""Check actual operation status and explicitly synthetic failure/stale views."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8768/site/daily.html');p.add_argument('--output',type=Path,required=True);p.add_argument('--chromium',required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=a.chromium,headless=True);page=browser.new_page(viewport={'width':1360,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    assert page.goto(a.url).status==200;page.get_by_role('link',name='打开完整日报').wait_for();page.get_by_role('link',name='查看本次运行证据').wait_for();page.get_by_role('link',name='健康检查证据').wait_for()
    assert '当前账户已更新' in page.locator('#health').inner_text();assert '最近归档' in page.locator('#health').inner_text()
    body=page.locator('#operation').inner_text();assert '最近运行成功' in body and 'enabled' in body and 'active' in body and 'yes' in body
    for href in page.locator('a[href]').evaluate_all('(n)=>n.map(x=>x.href)'):assert page.request.get(href).status==200,href
    page.screenshot(path=str(a.output/'operations-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth');page.screenshot(path=str(a.output/'operations-mobile.png'),full_page=True)
    # Browser-only routes; never alter the server, evidence or financial state.
    fixture=dict(phase='failed',mode='scheduled',operation='reports/operations/synthetic-test-only',started_at_utc='2026-01-01T00:00:00+00:00',finished_at_utc='2026-01-01T00:01:00+00:00',scheduler={})
    page.route('**/operation_status.json',lambda route:route.fulfill(json=fixture));page.reload();page.get_by_role('link',name='查看错误日志').wait_for();assert '最近运行失败' in page.locator('#operation').inner_text()
    fixture['phase']='running';page.reload();page.wait_for_function("document.querySelector('#operation').textContent.includes('超过15分钟')")
    health=dict(state='missed_schedule',actionable=True,issues=['missed_schedule','account_stale'],checked_at='2026-01-01T00:00:00+00:00',expected_through='2026-11-09')
    page.route('**/health_status.json',lambda route:route.fulfill(json=health));page.reload();page.wait_for_function("document.querySelector('#health').textContent.includes('定时任务漏跑')")
    assert '健康观察已过期' in page.locator('#health').inner_text()
    health['state']='notice_review_required';health['issues']=['notice_review_required'];page.reload();page.wait_for_function("document.querySelector('#health').textContent.includes('公告变化待审')")
    assert not errors;result=dict(actual_enabled_active_linger_view=True,actual_health_and_archive_visible=True,synthetic_missed_schedule_and_expired_health=True,synthetic_notice_review_visible=True,local_links_ok=True,mobile_no_overflow=True,synthetic_failure_and_stale_views=True,synthetic_views_do_not_modify_server=True,page_errors=errors)
    (a.output/'browser_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));browser.close()
