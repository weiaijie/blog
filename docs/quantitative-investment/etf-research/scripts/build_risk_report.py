"""Recompute read-only monitoring and an offline page from existing NAV files."""
from pathlib import Path
import argparse, hashlib, html, io, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from etf_research.risk_monitor import analyze, load_config
from etf_research.forward import digest, engine_digest

LABELS={'cash':'现金','equity_hold':'股票ETF持有','bond_hold':'债券ETF持有','monthly_20_80':'月度20/80','monthly_50_50':'月度50/50','trend_120':'120日趋势'}
ALERTS={'current_drawdown_warning':'当前回撤超过预警线','observed_year_drawdown_limit':'本年度已触及回撤上限','volatility_limit':'波动率未达控制标准','volatility_warning':'波动率超过预警线','var_limit':'VaR未达控制标准','sharpe_below_or_equal_target':'夏普未达目标','daily_move_warning':'单日涨跌超过预警线'}
def build(config_path, output, page):
    c=load_config(config_path,ROOT);results_path=ROOT/c['history_results'];saved=json.loads(results_path.read_text());hist=[];series={}
    sources={str(config_path.resolve().relative_to(ROOT)):hashlib.sha256(config_path.read_bytes()).hexdigest()}
    def source(path): sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    source(results_path);source(ROOT/c['protocol']);source(ROOT/c['forward_checkpoint'])
    original=ROOT/'docs/original-plan';catalog=json.loads((original/'sources.json').read_text());source(original/'sources.json')
    for f in catalog['files']:
        p=original/f['path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']: raise ValueError('Original plan hash mismatch')
        source(p)
    for run in saved['results']:
        p=results_path.parent/(run['run']+'_daily.csv');source(p);df=pd.read_csv(p,dtype={'date':str})
        if float(df['equity'].iloc[0])!=float(run['initial_cash']): raise ValueError('Missing initial valuation')
        metrics=analyze(df['date'],df['equity'],c['risk'])
        for key,oldkey in [('total_return','total_return'),('annualized_return','annualized_scenario_return'),('max_close_drawdown','max_close_drawdown')]:
            if not np.isclose(metrics[key],abs(run[oldkey]) if key=='max_close_drawdown' else run[oldkey],rtol=0,atol=1e-10):raise ValueError('Independent metric mismatch: '+run['run']+' '+key)
        hist.append({'run':run['run'],'strategy':run['strategy'],'scenario':run['scenario'],**metrics})
        if run['scenario']=='base':series[run['strategy']]=df
    checkpoint=json.loads((ROOT/c['forward_checkpoint']).read_text())
    if checkpoint['checkpoint_sha256']!=digest({k:v for k,v in checkpoint.items() if k!='checkpoint_sha256'}) or checkpoint['engine_sha256']!=engine_digest() or checkpoint['real_money'] is not False:
        raise ValueError('Forward checkpoint integrity failed')
    forward=[]
    for name,p in checkpoint['portfolios'].items():
        d=p['daily'];m=analyze([r['date'] for r in d],[r['equity'] for r in d],c['risk'])
        if m['sessions']!=checkpoint['forward_sessions'] or m['as_of']!=checkpoint['as_of']:raise ValueError('Forward date/count mismatch')
        forward.append({'run':name,**m})
    report={'schema_version':1,'mode':'report_only','changes_trades':False,'settings':c['risk'],
        'input_sha256':sources,'libraries':{'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__},
        'historical_cross_checks':len(hist)*3,'history':hist,'forward':forward,
        'methodology':'Daily close NAV including receivables; yearly drawdown anchored to previous observed year-end close; rolling sample standard deviation and historical linear-quantile VaR; zero risk-free rate is an assumption; insufficient windows stay null.'}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    # Stable offline SVG from a mature plotting library; no CDN or web API.
    plt.rcParams['svg.hashsalt']='etf-risk-v1';fig,ax=plt.subplots(figsize=(10,4))
    for name,df in series.items():
        nav=df['equity'];ax.plot(pd.to_datetime(df['date']),100*(1-nav/nav.cummax()),label=name,linewidth=1)
    ax.axhline(c['risk']['drawdown_warning']*100,color='orange',linestyle='--',label='warning');ax.axhline(c['risk']['annual_drawdown_limit']*100,color='red',linestyle=':',label='annual limit reference only')
    ax.set(ylabel='Drawdown from all-time close peak (%)',xlabel='Historical date');ax.legend(fontsize=7,ncol=2);fig.tight_layout()
    buf=io.StringIO();fig.savefig(buf,format='svg',metadata={'Date':None});plt.close(fig);svg=buf.getvalue();svg=svg[svg.index('<svg'):]
    def pct(x):return '样本不足 / 不适用' if x is None else f'{x:.2%}'
    rows=[]
    for r in hist:
        years='；'.join(f"{y['year']}: {pct(y['max_drawdown'])}" for y in r['years'] if y['limit_breached']) or '观测年份未触及'
        alerts='；'.join(ALERTS[k] for k in r['alerts']) or '当前未触发所列预警'
        rows.append('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in [LABELS[r['strategy']],r['scenario'],pct(r['max_close_drawdown']),pct(r['current_drawdown']),years,pct(r['rolling_volatility']),('不适用' if r['rolling_sharpe'] is None else f"{r['rolling_sharpe']:.2f}"),pct(r['daily_var']),alerts])+'</tr>')
    rf=c['risk'];thresholds=f"回撤超过 {pct(rf['drawdown_warning'])} 预警；年度最大回撤须低于 {pct(rf['annual_drawdown_limit'])}。年化波动率须低于 {pct(rf['annual_volatility_limit'])}，超过 {pct(rf['annual_volatility_warning'])} 预警。日 VaR（{rf['var_confidence']:.0%}）须低于 {pct(rf['daily_var_limit'])}；夏普目标 > {rf['sharpe_target']}。"
    text='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>计划对照与风险监控</title><style>body{font:16px/1.7 system-ui;margin:0;background:#f3f5f8;color:#182638}main{max-width:1200px;margin:auto;padding:24px}section{background:white;padding:22px;margin:18px 0;border-radius:12px}a{color:#165aad}.table{overflow-x:auto}table{border-collapse:collapse;min-width:1100px;width:100%}td,th{text-align:left;border-bottom:1px solid #ddd;padding:10px}svg{max-width:100%;height:auto}code{overflow-wrap:anywhere}.flow{display:flex;flex-wrap:wrap;gap:10px}.flow span{background:#e9eef9;padding:10px;border-radius:6px}</style><main><h1>计划对照与风险监控</h1><p>仅研究 · pandas / NumPy 分析 · matplotlib 绘图 · 预警不改变交易</p><a href="index.html">研究看板</a> · <a href="../docs/PLAN_ALIGNMENT.md">原计划逐项对照</a> · <a href="../config/research.json">统一监控配置</a> · <a href="../site/daily.html">每日运行状态</a><section><h2>系统怎么运作</h2><div class="flow"><span>来源 → 原始快照</span><span>多源 / 分红 / 日历核验</span><span>冻结历史研究与独立前瞻账户</span><span>成熟工具独立复核</span><span>风险报告与页面</span><span>测试 → GitHub → 备份</span></div><p>未通过数据核验就不更新。监控只读取结果，不能下单或修改已有目标。定时运行状态见每日入口，失败不会放宽核验。</p></section>'''
    text+='<section><h2>沿用原计划的风险标准</h2><p>'+thresholds+'</p><p>新增计算口径：最近 '+str(rf['lookback_returns'])+' 个日收益、样本标准差、历史分位数 VaR；无风险利率假设 '+pct(rf['annual_risk_free_assumption'])+'。这是文档标准的监控实现，不是已确认适合个人的风险偏好，也不是新增止损策略。</p></section>'
    text+='<section><h2>历史风险：截至 '+hist[0]['as_of']+'</h2><p>全区间回撤与年度回撤分开计算；年度以此前最后收盘净值为起点，首尾年份可能不完整。当前预警列指历史末日，不代表今天的账户状态。</p>'+svg+'<p>图中曲线为全区间峰值回撤，红色年度上限线仅作数值参考；是否年度超限以表中逐年计算为准。</p><div class="table"><table><thead><tr>'+''.join('<th>'+v+'</th>' for v in ['策略','费用','全区间最大回撤','历史末日回撤','年度触及上限','末252日年化波动','末252日夏普','末252日日VaR','历史末日监控'])+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></section>'
    text=text.replace('末252日','末'+str(rf['lookback_returns'])+'日')
    text+='<section><h2>前瞻账户单独监控</h2><p>截至 '+checkpoint['as_of']+'，'+str(checkpoint['forward_sessions'])+' 个观察日，'+str(len(forward))+' 个组合。252日样本不足时指标为空；空值不能当作低风险。完整指标见 JSON。</p></section><section><h2>仍未完成</h2><p>Beta、预设压力测试及官方季度持仓代理已接入；完整实时穿透未知。第三方引擎已做162场景对照，但现金边界差异阻止迁移。外部提醒、自动调度状态见每日入口。原计划股票/转债仓位和自动止损不会直接套到冻结 ETF 策略。原文历史业绩说法不是本项目已核验结果。</p><a href="../reports/2026-11-06-close/risk.json">下载完整监控结果</a> · <a href="../reports/2026-11-06-close/PROGRESS.md">本轮报告</a> · <a href="../reports/2026-11-07-rolling-risk/PROGRESS.md">18 个历史账户的连续预警和解除记录</a> · <a href="exposure.html">Beta、压力测试与披露持仓</a></section></main></html>'
    text=text.replace('252日样本',str(rf['lookback_returns'])+'日样本')
    page.parent.mkdir(parents=True,exist_ok=True);page.write_text(text)
    print('Risk monitor:',len(hist),'historical +',len(forward),'forward portfolios;',len(hist)*3,'independent metrics matched')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=ROOT/'config/research.json');p.add_argument('--output',type=Path,default=ROOT/'reports/2026-11-06-close/risk.json');p.add_argument('--page',type=Path,default=ROOT/'site/risk.html');a=p.parse_args();build(a.config,a.output,a.page)
