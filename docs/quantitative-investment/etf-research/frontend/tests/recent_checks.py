"""Exercise the recent-data workbench through real controls, at desktop/mobile widths."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, expect

p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
plan=dict(version=2,dataset='verified-2026-11-12',name='近期跨境核验',start='2026-11-02',end='2026-11-12',capital='100000',fees='base',rebalance='hold',model='allocation',installments='3',portfolios=['0,1,0,1','0,0,1,1','1,0,0,1'])
checks=[]
with sync_playwright() as pw:
    exe=Path(os.environ.get('LOCALAPPDATA',''))/'ms-playwright/chromium_headless_shell-1187/chrome-win/headless_shell.exe'
    browser=pw.chromium.launch(**({'executable_path':str(exe)} if exe.exists() else {}))
    for width in (1440,390):
        context=browser.new_context(viewport={'width':width,'height':960 if width==1440 else 844},reduced_motion='reduce')
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def open_plan(value,route='research'):
            page.goto(a.base+'/workbench/#/'+route+'?'+urlencode({'plan':json.dumps(value,ensure_ascii=False)}))
            expect(page.get_by_role('button',name='研究设置与保存')).to_be_visible()
        open_plan(plan)
        page.get_by_role('button',name='从第一天开始',exact=True).click()
        expect(page.get_by_text('已展示 1 /',exact=False)).to_be_visible(timeout=120000)
        page.get_by_role('button',name='下一交易日',exact=True).click()
        expect(page.get_by_text('已展示 2 /',exact=False)).to_be_visible(timeout=120000)
        link=page.get_by_role('link',name='Agent：当前请求JSON').get_attribute('href')
        assert link.startswith('/api/v2/')
        data=context.request.get(a.base+link,timeout=120000).json()
        order=next(r for r in data['frames'][1]['orders'] if r['symbol']=='513500')
        assert order['filled']==0 and order['reason']=='opening_halt'
        page.screenshot(path=str(a.output/f'opening-halt-{width}.png'))
        page.get_by_role('button',name='研究设置与保存').click()
        expect(page.get_by_role('combobox',name='数据版本',exact=True)).to_have_value('verified-2026-11-12')
        page.get_by_role('button',name='保存到本机').click()
        page.get_by_role('combobox',name='数据版本',exact=True).select_option('frozen-2026-10-30')
        page.get_by_role('combobox',name='本机已保存方案',exact=True).select_option(plan['name'])
        page.get_by_role('button',name='恢复所选方案').click()
        expect(page.get_by_role('combobox',name='数据版本',exact=True)).to_have_value('verified-2026-11-12')
        with page.expect_download() as download:page.get_by_role('button',name='导出Agent请求清单').click()
        exported=json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
        assert exported['dataVersion']==plan['dataset'] and exported['plan']==plan
        (a.output/f'agent-{width}.json').write_text(json.dumps(exported,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        page.get_by_role('button',name='应用设置',exact=True).click()
        comparison=dict(plan,start='2024-11-01')
        open_plan(comparison,'compare')
        page.get_by_role('button',name='运行比较',exact=True).click()
        expect(page.get_by_role('link',name='Agent：同一请求JSON')).to_be_visible(timeout=240000)
        link=page.get_by_role('link',name='Agent：同一请求JSON').get_attribute('href')
        result=context.request.get(a.base+link,timeout=240000).json()
        assert result['dataVersion']==plan['dataset']
        for i,year in enumerate(('1','2')):
            rows=page.locator('.comparison-block').nth(i).locator('tbody tr')
            assert rows.count()==3
            for j,portfolio in enumerate(result['portfolios']):
                stats=portfolio['periods'][year];cells=rows.nth(j).locator('td')
                assert [cells.nth(k).inner_text() for k in range(3)]==[str(stats[k]) for k in ('count','profitable','reached')]
                assert cells.nth(3).inner_text()==f"{float(stats['worstPnl']):,.2f}"
        page.locator('.comparison-block').nth(1).get_by_role('button').first.click()
        expect(page.get_by_role('link',name='明细JSON',exact=True)).to_be_visible(timeout=120000)
        detail=page.get_by_role('link',name='明细JSON',exact=True).get_attribute('href')
        overlay=context.request.get(a.base+detail,timeout=120000).json()
        assert overlay['dataVersion']==plan['dataset']
        selected=overlay['attribution']['dailyGaps']['B-A']['increases'][0]
        page.get_by_role('button',name=selected,exact=True).click()
        expect(page.get_by_role('combobox',name='核对交易日',exact=True)).to_have_value(selected)
        page.get_by_role('button',name='查看所选组合当日买卖与因子').click()
        expect(page.get_by_role('heading',name=selected+' · 交易与决策')).to_be_visible(timeout=120000)
        page.screenshot(path=str(a.output/f'worst-detail-{width}.png'))
        page.get_by_role('button',name='Close this dialog').click()
        for kind in ('methods','technical'):
            page.get_by_role('combobox',name='比较内容',exact=True).select_option(kind)
            page.get_by_role('button',name='运行比较',exact=True).click()
            expect(page.get_by_role('link',name='Agent：同一请求JSON')).to_be_visible(timeout=240000)
            page.locator('.comparison-block').nth(1).get_by_role('button').last.click()
            expect(page.get_by_role('link',name='明细JSON',exact=True)).to_be_visible(timeout=120000)
            page.get_by_role('button',name='查看模型当日买卖与因子').click()
            expect(page.locator('.el-drawer.open .factor-list li')).to_have_count(4 if kind=='technical' else 3,timeout=120000)
            page.get_by_role('button',name='Close this dialog').click()
        page.get_by_role('link',name='研究总览',exact=True).click()
        expect(page.get_by_role('heading',name='近期数据核验 · 2026-11-12')).to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(a.output/f'overview-{width}.png'))
        assert not errors,errors
        checks.append(dict(width=width,recentPlanRestored=True,agentVersionPreserved=True,openingHaltUnfilled=True,
                           windowsCountsExact=True,worstOverlayAttribution=True,methodAndTechnicalFactors=True,noOverflow=True,noPageErrors=True))
        context.close()
    browser.close()
(a.output/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks))
