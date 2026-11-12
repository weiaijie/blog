"""Additional no-sample, import, admission, and technical-model UI checks."""
import argparse,json,os
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright,expect
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
plan=dict(version=1,name='边界核验',start='2021-10-29',end='2022-03-01',capital='100000',fees='base',rebalance='hold',model='allocation',installments='3',portfolios=['1,0,0,1'])
with sync_playwright() as pw:
 executable=Path(os.environ.get('LOCALAPPDATA',''))/'ms-playwright/chromium_headless_shell-1187/chrome-win/headless_shell.exe'
 browser=pw.chromium.launch(**({'executable_path':str(executable)} if executable.exists() else {}));page=browser.new_page(viewport={'width':1440,'height':960},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def open_plan(p,route='compare'):
  page.goto(a.base+'/workbench/#/'+route+'?'+urlencode({'plan':json.dumps(p,ensure_ascii=False)}))
  expect(page.get_by_role('button',name='研究设置与保存')).to_be_visible()
 open_plan(plan);page.reload();page.get_by_role('button',name='运行比较',exact=True).click();expect(page.get_by_role('link',name='Agent：同一请求JSON')).to_be_visible(timeout=120000)
 assert page.get_by_text('无满期窗口',exact=True).count()==2
 page.get_by_role('button',name='研究设置与保存').click()
 page.get_by_label('导入方案JSON').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"version":99}'})
 expect(page.get_by_text('方案字段不完整，或含未知字段。',exact=True)).to_be_visible()
 expect(page.get_by_label('方案名称',exact=True)).to_have_value('边界核验')
 changed=dict(plan,name='已导入',capital='25000')
 page.get_by_label('导入方案JSON').set_input_files({'name':'valid.json','mimeType':'application/json','buffer':json.dumps(changed).encode()})
 expect(page.get_by_label('本金（元）',exact=True)).to_have_value('25000')
 page.get_by_role('button',name='生成复现链接').click();link=page.get_by_label('复现链接（含方案参数）').input_value();assert json.loads(__import__('urllib.parse').parse.parse_qs(link.split('?',1)[1])['plan'][0])==changed
 page.get_by_role('button',name='应用设置',exact=True).click();assert page.locator('.comparison-block').count()==0
 split=dict(plan,start='2021-10-29',end='2023-10-31',portfolios=['0,1,0,1'])
 open_plan(split,'research');page.get_by_role('button',name='计算完整区间',exact=True).click();expect(page.locator('.el-alert')).to_be_visible(timeout=120000);assert not page.get_by_role('link',name='Agent：当前请求JSON').count()
 technical=dict(plan,start='2019-03-20',end='2026-10-30',portfolios=['1,0,0,1','0,0,0,1'])
 open_plan(technical);page.get_by_role('combobox',name='比较内容',exact=True).select_option('technical');page.get_by_role('button',name='运行比较',exact=True).click();expect(page.get_by_role('link',name='Agent：同一请求JSON')).to_be_visible(timeout=120000)
 assert page.locator('.comparison-block').nth(1).locator('tbody tr').count()==4
 page.locator('.comparison-block').nth(1).get_by_role('button').last.click();expect(page.get_by_role('link',name='明细JSON',exact=True)).to_be_visible(timeout=120000)
 page.get_by_role('button',name='查看模型当日买卖与因子').click();expect(page.locator('.el-drawer .factor-list li')).to_have_count(4,timeout=120000)
 assert not errors,errors
 browser.close()
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(dict(shareReload=True,singlePortfolioNoMatureWindows=True,invalidImportPreservesPlan=True,validImportAndShare=True,parameterChangeClearsResults=True,splitGapFailsClosed=True,technicalWindowsAndFourFactors=True,noPageErrors=True),indent=2)+'\n',encoding='utf8');print('PASS boundary acceptance')
