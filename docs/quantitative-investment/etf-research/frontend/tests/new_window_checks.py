"""Verify all nine paired rows, threshold diagnosis, drilldowns and Agent parity on two viewports."""
import argparse,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);checks=[]
with sync_playwright() as pw:
    exe=Path(os.environ.get('LOCALAPPDATA',''))/'ms-playwright/chromium_headless_shell-1187/chrome-win/headless_shell.exe'
    browser=pw.chromium.launch(**({'executable_path':str(exe)} if exe.exists() else {}))
    for width in (1440,390):
        ctx=browser.new_context(viewport={'width':width,'height':960 if width==1440 else 844},reduced_motion='reduce')
        page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(a.base+'/workbench/#/changes')
        page.get_by_role('link',name='打开9个两年窗口归因 →').click(timeout=120000)
        expect(page.locator('.nine-table tbody tr')).to_have_count(9,timeout=120000)
        result=ctx.request.get(a.base+'/api/v2/backtest/new-window-attribution').json()
        for i,w in enumerate(result['windows']):
            row=page.locator('.nine-table tbody tr').nth(i)
            assert w['start']+' 至 '+w['end'] in row.inner_text()
            cells=row.locator('td')
            for j,m in enumerate(('allocation','multifactor_v1')):
                metric=w['metrics'][m]
                assert f"{float(metric['pnl']):,.2f}元" in cells.nth(j).inner_text()
                assert f"{float(metric['annualized_return'])*100:.2f}%" in cells.nth(j).inner_text()
                assert ('未达标' if not metric['reached'] else '· 达标') in cells.nth(j).inner_text()
            row.get_by_role('button').click()
            link=page.get_by_role('link',name='Agent：本期逐日明细JSON')
            expect(link).to_have_attribute('href','/api/v2/backtest/new-window-attribution-detail?case='+w['start'],timeout=120000)
            detail=ctx.request.get(a.base+link.get_attribute('href')).json()
            expected_day=detail['dailyGap']['decreases'][0]
            expect(page.get_by_role('combobox',name='核对交易日',exact=True)).to_have_value(expected_day)
            for j,m in enumerate(('allocation','multifactor_v1')):
                assert f"{float(detail['metrics'][m]['targetGap']):,.2f}" in page.locator('.threshold-table tbody tr').nth(j).inner_text()
            assert detail['difference']==w['difference']
        # Cost-borderline case and an actual factor switch, with prior-close signals.
        page.locator('.nine-table tbody tr').nth(3).get_by_role('button').click()
        expect(page.get_by_role('link',name='Agent：本期逐日明细JSON')).to_have_attribute('href','/api/v2/backtest/new-window-attribution-detail?case=2024-11-05',timeout=120000)
        detail=ctx.request.get(a.base+'/api/v2/backtest/new-window-attribution-detail?case=2024-11-05').json()
        frames=detail['replays']['multifactor_v1']['frames']
        switch=next(f['date'] for f in frames if any(o['side']=='sell' and o['filled'] for o in f['orders']))
        page.get_by_role('combobox',name='核对交易日',exact=True).select_option(switch)
        expect(page.locator('.factor-list li')).to_have_count(3)
        assert page.locator('.order-list li').count()>0
        page.get_by_role('heading',name='完整持有期的收益差额',exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(a.output/f'period-{width}.png'))
        page.get_by_role('combobox',name='核对交易日',exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(a.output/f'daily-{width}.png'))
        with page.expect_download() as dl:page.get_by_role('button',name='导出九期归因',exact=True).click()
        assert json.loads(Path(dl.value.path()).read_text(encoding='utf-8'))==result
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors,errors
        for query in ('?case=../comparison','?case=2024-11-05&capital=1','?case=2024-11-05&case=2024-11-06'):
            assert ctx.request.get(a.base+'/api/v2/backtest/new-window-attribution-detail'+query).status==400
        checks.append(dict(width=width,nineRowsExact=True,nineDetailsExact=True,targetGapsExact=True,
                           costBorderline=True,sellDayAndThreeFactors=True,exportExact=True,
                           invalidQueriesRejected=True,noOverflow=True,noPageErrors=True))
        ctx.close()
    browser.close()
(a.output/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks))
