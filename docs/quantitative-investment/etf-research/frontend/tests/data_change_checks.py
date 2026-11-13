"""Desktop/mobile controls and displayed statistics must match the version-comparison API."""
import argparse,json,os,re
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);checks=[]
with sync_playwright() as pw:
    exe=Path(os.environ.get('LOCALAPPDATA',''))/'ms-playwright/chromium_headless_shell-1187/chrome-win/headless_shell.exe'
    browser=pw.chromium.launch(**({'executable_path':str(exe)} if exe.exists() else {}))
    for width in (1440,390):
        context=browser.new_context(viewport={'width':width,'height':960 if width==1440 else 844},reduced_motion='reduce')
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(a.base+'/workbench/#/changes')
        expect(page.get_by_role('link',name='Agent：版本对比JSON')).to_be_visible(timeout=120000)
        result=context.request.get(a.base+'/api/v2/backtest/data-change').json()
        for group,count in [('domestic',7),('markets',4)]:
            page.get_by_role('combobox',name='比较范围',exact=True).select_option(group)
            scenarios=[s for s in result['scenarios'] if s['group']==group]
            for year in ('1','2'):
                page.get_by_role('combobox',name='持有期限',exact=True).select_option(year)
                rows=page.locator('.change-table tbody tr');expect(rows).to_have_count(count)
                for i,s in enumerate(scenarios):
                    d=s['periods'][year];cells=rows.nth(i).locator('td')
                    for j,key in enumerate(('count','profitable','reached')):
                        assert f"{d['before'][key]} → {d['after'][key]}" in cells.nth(j).inner_text()
                        signed=('+' if d['delta'][key]>0 else '')+str(d['delta'][key])
                        assert '（'+signed+'）' in cells.nth(j).inner_text()
                    assert f"{float(d['before']['worstPnl']):,.2f} → {float(d['after']['worstPnl']):,.2f}" in cells.nth(3).inner_text()
                    assert cells.nth(4).inner_text()=='0 / 0 / 0.00元'
        page.screenshot(path=str(a.output/f'cross-market-{width}.png'))
        page.get_by_role('button',name='标普500 / 国债',exact=True).click()
        expect(page.locator('.new-window-table tbody tr')).to_have_count(9)
        page.locator('.new-window-table tbody tr').first.get_by_role('button').click()
        expect(page.get_by_role('link',name='Agent：区间明细JSON')).to_be_visible(timeout=120000)
        link=page.get_by_role('link',name='Agent：区间明细JSON').get_attribute('href')
        detail=context.request.get(a.base+link).json()
        assert float(detail['counterfactual']['effect'])==0
        page.get_by_role('button',name='打开旧最差一期',exact=True).click()
        expect(page.get_by_role('link',name='Agent：区间明细JSON')).to_have_attribute('href',re.compile('worst-before'),timeout=120000)
        page.get_by_role('button',name='查看停牌拦单对照（未满一年）',exact=True).click()
        expect(page.get_by_role('link',name='Agent：区间明细JSON')).to_have_attribute('href',re.compile('diagnostic'),timeout=120000)
        expect(page.get_by_role('combobox',name='核对交易日',exact=True)).to_have_value('2026-11-03')
        expect(page.locator('.order-list').get_by_text('开盘停牌',exact=False)).to_be_visible()
        link=page.get_by_role('link',name='Agent：区间明细JSON').get_attribute('href')
        diagnostic=context.request.get(a.base+link).json()
        assert float(diagnostic['counterfactual']['effect'])==108.97
        expect(page.get_by_text('按公告执行 减 假设忽略新增停牌：+108.97元。',exact=False)).to_be_visible()
        assert any(o['symbol']=='513500' and o['filled']==0 for f in diagnostic['actual']['frames'] for o in f['orders'])
        page.get_by_role('heading',name='整个区间的条件差额').scroll_into_view_if_needed()
        page.screenshot(path=str(a.output/f'halt-attribution-{width}.png'))
        page.get_by_role('combobox',name='比较范围',exact=True).select_option('domestic')
        page.get_by_role('button',name='三因子＋ADX',exact=True).click()
        page.locator('.new-window-table tbody tr').first.get_by_role('button').click()
        expect(page.locator('.factor-list li')).to_have_count(4,timeout=120000)
        with page.expect_download() as download:page.get_by_role('button',name='导出对比',exact=True).click()
        assert json.loads(Path(download.value.path()).read_text(encoding='utf-8'))==result
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors,errors
        checks.append(dict(width=width,all22StatsRowsExact=True,newWindowsNineEach=True,oldWorstVersion=True,
                           haltPositiveControl=True,dailyAttribution=True,adxFactors=True,exportExact=True,noOverflow=True,noPageErrors=True))
        context.close()
    browser.close()
(a.output/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks))
