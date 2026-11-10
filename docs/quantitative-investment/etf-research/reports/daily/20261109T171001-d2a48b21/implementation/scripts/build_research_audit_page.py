"""Offline research evidence page and exportable figure; no live account changes."""
from pathlib import Path
import argparse,csv,html,json,sys
ROOT=Path(__file__).resolve().parents[1]
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def pct(value):return '未知' if value is None else f'{float(value):.2%}'


def build(output,page):
    h=json.loads((output/'horizons.json').read_text(encoding='utf-8'))
    holdings=json.loads((output/'holdings.json').read_text(encoding='utf-8'))
    cross=json.loads((output/'horizon_crosscheck.json').read_text(encoding='utf-8'))
    calendar=json.loads((output/'calendar_readiness.json').read_text(encoding='utf-8'))
    main=[r for r in h['continuous'] if r['run']==h['settings']['main_run']]
    fresh=[r for r in h['fresh'] if r['scenario']=='base']
    df=pd.read_csv(output/'continuous_windows.csv');df=df[df.run==h['settings']['main_run']]
    new=pd.read_csv(output/'fresh_accounts.csv');new=new[new.scenario=='base']
    plt.rcParams['svg.hashsalt']='etf-horizon-v1'
    fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True)
    for ax,years in zip(axes,(1,2)):
        old=df[df.years==years];f=new[new.years==years]
        ax.plot(pd.to_datetime(old.start),old.annualized_return*100,label='Continuous account window',linewidth=1.2)
        ax.scatter(pd.to_datetime(f.start),f.annualized_return*100,label='Fresh monthly entry',s=10,color='#b45309')
        ax.axhline(4,color='#147d64',linestyle='--',label='4% reference');ax.axhline(5,color='#8b5cf6',linestyle=':',label='5% reference');ax.axhline(0,color='#94a3b8',linewidth=.7)
        ax.set(ylabel='Annualized return (%)',title=f'{years} calendar year(s), fixed monthly 50/50, base costs')
        ax.grid(alpha=.15);ax.legend(fontsize=7,ncol=2)
    axes[-1].set_xlabel('Window start date (historical, overlapping samples)');fig.tight_layout()
    fig.savefig(output/'holding_windows.svg',metadata={'Date':None});plt.close(fig)
    def cells(r,label):
        q=r['annualized_quantiles'];n=r['count']
        return [label,str(r['years']),str(n),f"{r['at_least_4pct']}/{n} ({pct(r['at_least_4pct']/n)})",f"{r['at_least_5pct']}/{n} ({pct(r['at_least_5pct']/n)})",f"{r['losses']}/{n} ({pct(r['losses']/n)})",pct(q['median']),pct(q['min'])+' ～ '+pct(q['max']),pct(r['worst_window_drawdown'])]
    headers=['账户 / 费用','年数','完整窗口','年化≥4%','年化≥5%','亏损窗口','年化中位数','年化最小～最大','最差窗口回撤']
    main_rows=[cells(r,'连续 / base') for r in main]+[cells(r,'新入场 / base') for r in fresh]
    all_rows=[cells(r,r['run'].replace('_100000_d1','')) for r in h['continuous']]
    def table(rows):return '<div class="table"><table><thead><tr>'+''.join('<th scope="col">'+html.escape(v)+'</th>' for v in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    report_rel='reports/2026-11-06-research-audit';link='../'+report_rel+'/'
    stock=holdings['stock'];bond=holdings['bond']
    phases=[r for r in h['disjoint'] if r['run']==h['settings']['main_run']]
    phase_text=[]
    for years in (1,2):
        group=[r for r in phases if r['years']==years]
        phase_text.append(f"{years}年：每组 {min(r['count'] for r in group)}～{max(r['count'] for r in group)} 个窗口，组内年化≥4%的历史占比 {pct(min(r['at_least_4pct']/r['count'] for r in group))}～{pct(max(r['at_least_4pct']/r['count'] for r in group))}")
    issue_text='；'.join(k+'：至少占净资产 '+pct(v) for k,v in bond['known_issue_nav_lower_bounds'].items())
    text='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>目标可行性与持仓证据审计</title><style>body{font:16px/1.75 system-ui,sans-serif;margin:0;color:#182638;background:#f3f5f8}main{max-width:1180px;margin:auto;padding:24px}section{background:#fff;padding:24px;margin:20px 0;border-radius:12px}a{color:#165aad}h1{line-height:1.3}h2{line-height:1.4}.tag{color:#526174}strong{color:#8c3414}.table{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:1060px}th,td{padding:10px;border-bottom:1px solid #dce1e8;text-align:left;font-variant-numeric:tabular-nums}th{background:#eef2f8}img{max-width:100%;height:auto}li{margin:8px 0}code{overflow-wrap:anywhere}nav{display:flex;flex-wrap:wrap;gap:14px}@media(max-width:600px){main{padding:14px}section{padding:16px}h1{font-size:27px}}</style></head><body><main><p class="tag">个人量化研究 · 历史证据审计 · 2026-11-06启动 / 11-07核验</p><h1>4%～5%目标，历史证据支持到什么程度？</h1><nav><a href="index.html">历史看板</a><a href="daily.html">每日状态</a><a href="risk.html">风险标准</a><a href="exposure.html">季度披露代理</a></nav>'''
    text+='<section><h2>目前结论：不能据此确认长期目标可稳定实现</h2><p>历史数据截至 2026-10-30。固定月度50/50组合全期年化约4.02%，但一年、两年窗口中存在明显亏损和起点差异。以下是历史样本占比，<strong>不是未来成功概率</strong>。新计算没有调参、选优，也没有增加前瞻观察日。</p>'+table(main_rows)+'</section>'
    text+='<section><h2>相同策略，不同入场时点</h2><img src="'+link+'holding_windows.svg" alt="固定50/50组合一年和两年窗口年化随开始日期变化，连续账户曲线与新入场账户散点"><p>蓝线继承原账户持仓与现金；橙点是每个完整可观察月份首个交易日从10万元现金开始的账户，首日观察、下一交易日才执行。两类问题分别展示。均包含冻结模型交易费用和滑点，期末不强制卖出，未计期末变现费用。</p><p>周年日不是交易日时，取之后首个已核验交易日；按实际日数 / 365.25 年化。未满完整持有期的尾部样本排除。窗口回撤从窗口起点重新计峰，不能替代原年度回撤标准。</p></section>'
    text+='<section><h2>重叠样本与全部费用场景</h2><p>每日滚动窗口高度重叠。另按12个月偏移分别构造组内不重叠窗口，12组之间仍相关，不合并为独立样本，也不据此给出置信概率。</p><ul>'+''.join('<li>'+v+'</li>' for v in phase_text)+'</ul><p>下面公开全部18个原固定账户（6策略 × 3费用），本金10万元、延迟1个交易日；原162场景保持原样，本次窗口审计没有扩展为162场景优化。</p>'+table(all_rows)+'</section>'
    text+='<section><h2>官方中期持仓：截至2026-06-30</h2><p>两份中期财务报表注明未经审计，分别于8月29日、8月31日公告。六月末完整股票表与九月末季度摘要是不同观察时点，均不能称当前持仓，也不回填成历史持仓序列。</p><p>510300：核对300项指数投资和39项积极投资，共339个证券代码。逐表金额精确对齐，股票资产 '+pct(stock['stock_fraction_of_nav'])+' / 净资产，'+pct(stock['stock_fraction_of_assets'])+' / 总资产；两个分母不可混用。前十大占净资产 '+pct(stock['top10_fraction_of_nav'])+'。股票部分 HHI '+f"{float(stock['stock_sleeve_hhi']):.6f}"+'，等效证券数 '+f"{float(stock['stock_sleeve_effective_count']):.2f}"+'；这不是全基金或最终发行人集中度。</p><p>511010：国家债券占净资产 '+pct(bond['government_bond_fraction_of_nav'])+'。披露的前五代码只覆盖债券资产 '+pct(bond['listed_fraction_of_bonds'])+'，完整证券 HHI 保持未知。官方跨市场代码映射归并后为三期已知国债：'+issue_text+'。财政部发行人风险不能按五个代码分散计算。</p><p>九月末前五代码也可归并为三期国债，单独结果见持仓 JSON；不得把六月权重与九月权重拼接。</p><a href="'+link+'holdings.json">金额、分母、代码映射与原文页码</a> · <a href="'+link+'stocks_2026h1.csv">339项股票明细</a> · <a href="../data/snapshots/2026-11-06-research-evidence-234940/interim_510300.pdf">510300官方原文快照</a> · <a href="../data/snapshots/2026-11-06-research-evidence-234940/interim_511010.pdf">511010官方原文快照</a></section>'
    text+='<section><h2>跨年准备与工程证据</h2><p>本轮未取得2027年官方日历；索引快照未出现2027，不等于证明所有官方渠道尚未发布。现有日历仅覆盖至2026年。5个模拟边界检查通过，2027年缺少证据时，健康检查和数据准入均阻断，不把未知年份当休市。</p><p>标准库 / Decimal 独立核对 '+str(cross['numeric_fields_checked'])+' 个数值字段、'+str(cross['summary_groups_checked'])+' 组摘要；255个新账户首日现金及信号时序另行检查。既有历史、协议、前瞻账户和11月6日目标均保留。</p><ul>'+''.join('<li><a href="'+link+name+'">'+label+'</a></li>' for name,label in [('horizons.json','全部分组、分位数与来源哈希'),('continuous_windows.csv','57,726个连续账户窗口'),('fresh_accounts.csv','474个新入场持有期结果'),('disjoint_windows.csv','2,232个分组内不重叠窗口'),('horizon_crosscheck.json','独立复核结果'),('calendar_readiness.json','跨年证据与阻断验收'),('PROGRESS.md','本轮交付与限制')])+'</ul></section></main></body></html>'
    page.parent.mkdir(parents=True,exist_ok=True);page.write_text(text,encoding='utf-8')
    lines=['# 目标可行性与风险证据审计','','启动2026-11-06，计算与原文核验2026-11-07。仅研究；不改变冻结策略、历史结果、前瞻账户或既有目标。','','## 一年、两年目标证据','','连续账户窗口继承持仓；新入场账户从现金开始，二者不混用。所有窗口是历史重叠样本，占比不是未来概率；不据此调参或推荐交易。','','| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']
    lines+=['| '+' | '.join(row)+' |' for row in main_rows]
    lines+=['','12个偏移组内不重叠，组间仍相关：']+['- '+v for v in phase_text]
    lines+=['','完整18账户、36个连续摘要、432个不重叠分组摘要和6个新入场摘要见horizons.json。57,726连续窗口、2,232分组窗口、474新入场持有期，255个新账户。独立Decimal逐窗核对291,000数值字段；另核对474组摘要和信号时序。','',
        '## 官方披露与集中度','',f"510300完整披露股票339项，金额精确核对至分，股票占净资产{pct(stock['stock_fraction_of_nav'])}，占总资产{pct(stock['stock_fraction_of_assets'])}；前十大占净资产{pct(stock['top10_fraction_of_nav'])}。股票部分HHI {float(stock['stock_sleeve_hhi']):.6f}，等效证券数{float(stock['stock_sleeve_effective_count']):.2f}，不能冒称全基金/最终发行人HHI。",'',f"511010前五代码覆盖债券资产{pct(bond['listed_fraction_of_bonds'])}，归并为三期债券：{issue_text}。未披露债券金额{bond['undisclosed_bond_value']}元；完整证券集中度未知。国家债券占净资产{pct(bond['government_bond_fraction_of_nav'])}，发行人集中不可按代码分散。",'',
        '两份2026中期财务报表均未经审计；PDF第13/14页资产减负债等于净资产。510300第48–56页完整股票表逐行解析、逐表合计，511010第35页前两行末位数字换行，已渲染原页人工核对并以文本片段约束。持仓截止6月30日，公告8月29/31日；Q3代理截止9月30日，分别保留，不混拼时点。官方身份API于11月7日获取，仅用于代码身份核验，不代表持仓权重当日有效。','',
        '## 日历和来源限制','','本轮官方休市索引未取得2027证据，不声称全球未发布。5项模拟边界检查与跨年准入阻断通过，未生成猜测交易日。后续取得官方通知后需新快照、独立复核及版本化加载迁移。','',
        '首次PDF采集因Ubuntu缺少pdftotext中断；原始字节、失败说明保留，因请求元数据不全排除分析。随后使用pypdf取得完整请求证据。债券静态HTML仅有模板，保留但不当映射证据；实际依据官方页面JS指向的COMMON_BOND_BASIC_ZQJBYS_L响应。','',
        '## 复现','','运行build_horizon_audit.py、check_horizon_audit.py、build_holdings_audit.py、check_calendar_readiness.py、build_research_audit_page.py。输出可指定新目录；核心输入和旧报告不覆盖。pandas/NumPy负责批量分析，Decimal独立复核，matplotlib生成可导出SVG。PDF原文提取使用pypdf6.21.4，视觉核对PyMuPDF1.26.7，仅取证工具，不是运行管线新依赖。','',
        '工程验收、部署和Git持久化结果另见VALIDATION.md。下一新增交易日仍需11月9日16:00后实际来源准入，不能由本轮研究代替无人值守跨日验收。外部提醒、实时完整穿透和框架迁移仍未完成。','']
    (output/'PROGRESS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Built offline research page, SVG and evidence report')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'reports/2026-11-06-research-audit');p.add_argument('--page',type=Path,default=ROOT/'site/research-audit.html');a=p.parse_args();build(a.output,a.page)
