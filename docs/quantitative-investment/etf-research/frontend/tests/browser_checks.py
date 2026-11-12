"""Browser acceptance using the existing Python Playwright installation.

Run against an isolated server first. The baseline is the previous dashboard API.
Writes screenshots and a compact evidence JSON, never modifies research accounts.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, expect

parser=argparse.ArgumentParser()
parser.add_argument('--base',required=True)
parser.add_argument('--baseline',required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
plan=dict(version=1,name='验收方案',start='2021-10-29',end='2023-10-31',capital='100000',fees='base',rebalance='hold',model='multifactor_adx_v1',installments='3',portfolios=['1,0,0,1','0,0,0,1'])
checks=[]

with sync_playwright() as pw:
    executable=Path(os.environ.get('LOCALAPPDATA',''))/'ms-playwright/chromium_headless_shell-1187/chrome-win/headless_shell.exe'
    browser=pw.chromium.launch(**({'executable_path':str(executable)} if executable.exists() else {}))
    for width in (1440,390):
        context=browser.new_context(reduced_motion='reduce',viewport={'width':width,'height':960 if width==1440 else 844})
        page=context.new_page();errors=[];requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append(r.url))
        def open_plan(route,p):
            page.goto(args.base+'/workbench/#/'+route+'?'+urlencode({'plan':json.dumps(p,ensure_ascii=False)}))
            expect(page.get_by_role('button',name='研究设置与保存')).to_be_visible()
        open_plan('research',plan)
        page.get_by_role('button',name='从第一天开始',exact=True).click()
        expect(page.get_by_text('已展示 1 /',exact=False)).to_be_visible(timeout=120000)
        endpoint=page.get_by_role('link',name='Agent：当前请求JSON').get_attribute('href')
        result=context.request.get(args.base+endpoint).json()
        baseline=context.request.get(args.baseline+endpoint).json()
        assert result==baseline and len(result['frames'])==1
        assert result['frames'][0]['date']==plan['start']
        assert all(r['filled']==0 for r in result['frames'][0]['orders'])
        assert not any('step=all' in u for u in requests)
        page.get_by_role('button',name='下一交易日',exact=True).click()
        expect(page.get_by_text('已展示 2 /',exact=False)).to_be_visible(timeout=120000)
        page.screenshot(path=str(args.output/f'replay-{width}.png'))
        page.get_by_role('button',name='计算完整区间',exact=True).click()
        expect(page.get_by_role('link',name='Agent：当前请求JSON')).to_have_attribute('href',__import__('re').compile('step=all'),timeout=120000)
        endpoint=page.get_by_role('link',name='Agent：当前请求JSON').get_attribute('href')
        result=context.request.get(args.base+endpoint).json()
        assert result==context.request.get(args.baseline+endpoint).json()
        assert result['step']==result['totalSessions']
        assert page.locator('.stats').first.inner_text().find(f"{float(result['frames'][-1]['pnl']):,.2f}")>=0
        page.get_by_role('button',name='研究设置与保存').click()
        page.get_by_label('方案名称',exact=True).fill('验收保存')
        page.get_by_role('button',name='保存到本机',exact=True).click()
        page.get_by_label('本金（元）',exact=True).fill('200000')
        page.get_by_role('combobox',name='本机已保存方案',exact=True).select_option('验收保存')
        page.get_by_role('button',name='恢复所选方案',exact=True).click()
        expect(page.get_by_label('本金（元）',exact=True)).to_have_value('100000')
        with page.expect_download() as dl:
            page.get_by_role('button',name='导出Agent请求清单',exact=True).click()
        exported=json.loads(Path(dl.value.path()).read_text())
        assert exported['plan']['name']=='验收保存'
        assert 'rebalance=signal' in exported['requests']['replay']
        page.get_by_role('button',name='删除所选方案',exact=True).click()
        page.get_by_role('button',name='撤销删除',exact=True).click()
        assert '验收保存' in page.get_by_role('combobox',name='本机已保存方案',exact=True).inner_text()
        page.get_by_role('button',name='应用设置',exact=True).click()
        expect(page.get_by_text('尚未运行。',exact=False)).to_be_visible()
        page.get_by_role('link',name='组合比较',exact=True).click()
        page.get_by_role('button',name='运行比较',exact=True).click()
        expect(page.get_by_role('link',name='Agent：同一请求JSON')).to_be_visible(timeout=180000)
        endpoint=page.get_by_role('link',name='Agent：同一请求JSON').get_attribute('href')
        comparison=context.request.get(args.base+endpoint).json()
        assert comparison==context.request.get(args.baseline+endpoint).json()
        for i,year in enumerate(('1','2')):
            rows=page.locator('.comparison-block').nth(i).locator('tbody tr')
            for j,p in enumerate(comparison['portfolios']):
                stats=p['periods'][year];cells=rows.nth(j).locator('td')
                assert cells.nth(0).inner_text()==str(stats['count'])
                assert cells.nth(1).inner_text()==str(stats['profitable'])
                assert cells.nth(2).inner_text()==str(stats['reached'])
                assert cells.nth(3).inner_text()==f"{float(stats['worstPnl']):,.2f}"
        page.locator('.comparison-block').first.get_by_role('button').first.click()
        expect(page.get_by_role('link',name='明细JSON',exact=True)).to_be_visible(timeout=120000)
        endpoint=page.get_by_role('link',name='明细JSON',exact=True).get_attribute('href')
        overlay=context.request.get(args.base+endpoint).json()
        assert overlay==context.request.get(args.baseline+endpoint).json()
        selected=overlay['attribution']['dailyGaps']['B-A']['increases'][0]
        page.get_by_role('button',name=selected,exact=True).click()
        expect(page.get_by_role('combobox',name='核对交易日',exact=True)).to_have_value(selected)
        page.get_by_role('combobox',name='统计区间',exact=True).select_option('drawdown')
        expected=overlay['attribution']['peakToTrough']['A']['differences']['B-A']['totals']['net']
        expect(page.get_by_text(f'净贡献合计 {float(expected):,.2f} 元。',exact=False)).to_be_visible()
        page.get_by_role('button',name='查看所选组合当日买卖与因子').click()
        expect(page.get_by_role('heading',name=selected+' · 交易与决策')).to_be_visible(timeout=120000)
        box=page.locator('.el-drawer.open').bounding_box()
        assert box and abs(box['y'])<1 and box['x']>=-1 and box['x']+box['width']<=width+1,box
        page.screenshot(path=str(args.output/f'detail-{width}.png'))
        page.get_by_role('button',name='Close this dialog').click()
        page.get_by_role('combobox',name='比较内容',exact=True).select_option('methods')
        page.get_by_role('button',name='运行比较',exact=True).click()
        expect(page.get_by_role('link',name='Agent：同一请求JSON')).to_be_visible(timeout=120000)
        page.locator('.comparison-block').first.get_by_role('button').last.click()
        expect(page.get_by_role('link',name='明细JSON',exact=True)).to_be_visible(timeout=120000)
        page.get_by_role('button',name='查看模型当日买卖与因子').click()
        expect(page.get_by_role('heading',name='今天收盘后的决定')).to_be_visible(timeout=120000)
        page.get_by_role('button',name='Close this dialog').click()
        page.get_by_role('link',name='研究总览',exact=True).click()
        expect(page.get_by_text('真正前瞻观察',exact=True)).to_be_visible()
        page.screenshot(path=str(args.output/f'overview-{width}.png'))
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.get_by_role('link',name='行情与数据',exact=True).click()
        expect(page.get_by_role('heading',name='逐只核验范围')).to_be_visible()
        assert page.locator('tbody tr').count()==4
        assert not errors,errors
        # Only one options request throughout all page transitions.
        assert sum('/api/v1/backtest/options' in u for u in requests)==1
        checks.append(dict(width=width,firstStepNoFuture=True,fullReplayExactBaseline=True,comparisonCountsExact=True,overlayExactBaseline=True,savedPlanRestored=True,agentExport=True,attributionAndTradingDrawer=True,modelWorstFactors=True,noOverflow=True,noPageErrors=True,optionsRequests=1))
        context.close()
    browser.close()
(args.output/'browser-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False))
