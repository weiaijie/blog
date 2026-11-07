"""Historical/prospective beta, disclosed holdings and fixed current stress page."""
from pathlib import Path
from datetime import date
from decimal import Decimal as D
import argparse,hashlib,html,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import pandas as pd
from etf_research.long_history import load_long_history
from etf_research.admission import load_incremental
from etf_research.forward import digest,engine_digest
from etf_research.risk_extensions import benchmark_returns,beta_metrics,exposure_stress
from etf_research.bond_issues import identity_map, issue_exposures

def build(output,page,config_path=ROOT/'config/research.json',extra_path=ROOT/'config/risk_extensions.json'):
    config=json.loads(config_path.read_text());extra=json.loads(extra_path.read_text())
    if extra['mode']!='report_only' or extra['lookback_returns']!=252:raise ValueError('Unexpected analysis protocol')
    historic=load_long_history(ROOT/'data/snapshots');current,_=load_incremental(ROOT/'data/snapshots',extra['forward_price_snapshot'])
    state=json.loads((ROOT/config['forward_checkpoint']).read_text())
    if digest({k:v for k,v in state.items() if k!='checkpoint_sha256'})!=state['checkpoint_sha256'] or engine_digest()!=state['engine_sha256']:raise ValueError('Checkpoint integrity mismatch')
    if str(current.sessions[-1])!=state['as_of']:raise ValueError('Prices and checkpoint disagree')
    disclosure=json.loads((ROOT/extra['holdings_reference']).read_text())
    identity_source = extra.get('bond_identity_snapshot')
    identities = identity_map(ROOT / identity_source) if identity_source else None
    for fund in disclosure['funds'].values():
        if hashlib.sha256((ROOT/fund['pdf_path']).read_bytes()).hexdigest()!=fund['pdf_sha256']:raise ValueError('Official holdings PDF changed')
        if fund['announcement_date']>state['as_of']:raise ValueError('Future disclosure is unavailable')
    benchmarks={s:benchmark_returns(historic,s) for s in ('510300','511010')};forward_benchmarks={s:benchmark_returns(current,s) for s in benchmarks}
    historical=[];forward=[]
    saved=ROOT/config['history_results']
    for row in json.loads(saved.read_text())['results']:
        df=pd.read_csv(saved.parent/(row['run']+'_daily.csv'))
        historical.append(dict(run=row['run'],as_of=str(historic.sessions[-1]),beta={s:beta_metrics(df['date'],df['equity'],b) for s,b in benchmarks.items()}))
    day=current.sessions[-1]
    for name,portfolio in state['portfolios'].items():
        daily=portfolio['daily'];last=daily[-1];equity=D(last['equity'])
        values={s:D(last['units_'+s])*current.bars[s][day].close for s in benchmarks}
        if sum(values.values())+D(last['cash'])+D(last['receivables'])!=equity:raise ValueError('Exposure does not reconcile to NAV')
        lookthrough={}
        for s,fund in disclosure['funds'].items():
            weight=values[s]/equity
            lookthrough[s]=dict(etf_weight=str(weight),disclosure_as_of=fund['report_date'],disclosure_age_days=(day-date.fromisoformat(fund['report_date'])).days,
                exact_current_holdings=None,listed_positions_proxy=[dict(code=x['code'],name=x['name'],portfolio_fraction=str(weight*D(x['nav_fraction']))) for x in fund['listed_positions']],
                unlisted_security_proxy_fraction=str(weight*D(fund['unlisted_security_nav_fraction'])),
                sector_proxy={k:dict(name=v['name'],portfolio_fraction=str(weight*D(v['nav_fraction']))) for k,v in fund['sectors'].items()})
            if 'issuer_category' in fund:lookthrough[s]['issuer_proxy']=dict(name=fund['issuer_category']['name'],portfolio_fraction=str(weight*D(fund['issuer_category']['nav_fraction'])))
            if s == '511010' and identities is not None:
                lookthrough[s]['disclosed_issues'] = issue_exposures(fund, identities, values[s], equity)
        forward.append(dict(run=name,as_of=state['as_of'],equity=str(equity),beta={s:beta_metrics([r['date'] for r in daily],[r['equity'] for r in daily],b) for s,b in forward_benchmarks.items()},stress=exposure_stress(equity,values,extra['stress_scenarios']),lookthrough=lookthrough))
    result=dict(schema_version=1,mode='report_only',changes_trades=False,benchmark_method='ETF gross total-return proxy from unadjusted close plus official ex-date cash dividend; fractional reinvestment, no fees. Not CSI300 or official bond index returns.',beta_method='Last 252 paired daily returns, sample covariance / benchmark variance; insufficient forward samples remain null.',holdings_method='2026Q3 disclosed weights applied to current ETF exposure as a dated proxy only; top code rows not full portfolio, bond cross-market aliases not consolidated.',stress_method=extra['stress_scope'],history=historical,forward=forward,disclosure=disclosure,input_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in (str(config_path.relative_to(ROOT)),str(extra_path.relative_to(ROOT)),config['forward_checkpoint'],extra['holdings_reference'])})
    if identities is not None:
        result['holdings_method'] = 'Q3 disclosed codes grouped by verified issue; lower bounds at disclosure date applied to account ETF value.'
        result['bond_identity_snapshot'] = identity_source
        manifest = identity_source + '/manifest.json'
        result['input_sha256'][manifest] = hashlib.sha256((ROOT/manifest).read_bytes()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    esc=html.escape;main=next(x for x in forward if x['run']=='monthly_50_50_base')
    body='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>组合风险扩展</title><link rel="stylesheet" href="style.css"><main><h1>组合风险扩展</h1><p>只分析，不改变冻结策略或交易。</p><a href="index.html">研究看板</a> · <a href="risk.html">风险标准</a>'
    body+='<section><h2>历史 Beta · 截至 '+str(historic.sessions[-1])+'</h2><p>最近252个日收益；基准为各ETF原价加官方分红构造的无费用再投资代理，并非官方指数。前瞻只有'+str(state['forward_sessions'])+'个观察日；不足252个收益时Beta为空，不借历史补足。</p><div class="table-wrap"><table><thead><tr><th>组合</th><th>对股票ETF Beta</th><th>对债券ETF Beta</th></tr></thead><tbody>'
    for row in historical:body+='<tr><td>'+esc(row['run'])+'</td>'+''.join('<td>'+('样本不足' if row['beta'][s]['beta'] is None else f"{row['beta'][s]['beta']:.4f}")+'</td>' for s in benchmarks)+'</tr>'
    body+='</tbody></table></div></section><section><h2>主观察组合压力情景 · '+state['as_of']+'</h2><p>预设一次性价格冲击，持仓不变、现金不变；不含成交、流动性、费用和再平衡，不是预测或损失上限。</p><div class="table-wrap"><table><tr><th>情景</th><th>估算损益（元）</th><th>组合变化</th></tr>'
    for row in main['stress']:body+='<tr><td>'+esc(row['name'])+'</td><td>'+f"{D(row['pnl']):.2f}"+'</td><td>'+f"{D(row['return_fraction']):.2%}"+'</td></tr>'
    body+='</table></div></section><section><h2>穿透资料 · 2026-09-30披露持仓</h2><p>公告日期2026-10-27，距当前账户日期'+str(main['lookthrough']['510300']['disclosure_age_days'])+'天。仅作最近披露代理，当前实际穿透持仓仍未知；禁止用本资料回填历史。</p>'
    for code,fund in disclosure['funds'].items():
        body+='<h3>'+code+'</h3><p>已披露的前'+str(len(fund['listed_positions']))+'条证券代码占基金净资产 '+f"{D(fund['listed_nav_fraction']):.2%}"+'；未逐项列出的证券占 '+f"{D(fund['unlisted_security_nav_fraction']):.2%}"+'。完整证券集中度不计算。</p>'
        if code=='510300':body+='<p>基金制造业披露权重 '+f"{D(fund['sectors']['C']['nav_fraction']):.2%}"+'，主观察组合制造业代理暴露 '+f"{D(main['lookthrough'][code]['sector_proxy']['C']['portfolio_fraction']):.2%}"+'。</p>'
        elif identities is not None:
            body += '<p>按三季报公允价值与官方代码映射归并。以下为主观察账户按披露持仓估算的敞口，只覆盖前五个代码。</p><div class="table-wrap"><table><tr><th>国债期次及原代码</th><th>占基金净资产</th><th>组合敞口（元）</th><th>占组合净值</th></tr>'
            for issue in main['lookthrough'][code]['disclosed_issues']:
                label = esc(issue['issue'] or '期次未知') + ' · ' + esc(' / '.join(issue['codes']))
                body += f'<tr><td>{label}</td><td>{D(issue["fund_fraction"]):.2%}</td><td>{D(issue["portfolio_amount"]):,.2f}</td><td>{D(issue["portfolio_fraction"]):.2%}</td></tr>'
            body += '</table></div><p>当期未披露的各券权重未知。代码身份于11月7日核验。</p>'
        else:body+='<p>国家债券占基金净资产 '+f"{D(fund['issuer_category']['nav_fraction']):.2%}"+'。前五条含可能跨市场对应同一期国债的代码，未核实映射前不声称五个独立风险来源。</p>'
        body+='<a href="../'+esc(fund['pdf_path'])+'">官方季报原文</a> · <a href="'+esc(fund['official_url'])+'">上交所来源</a>'
    body+='</section><p><a href="../'+esc(extra['published_report'])+'">全部组合与计算结果</a></p></main></html>'
    page.parent.mkdir(parents=True,exist_ok=True);page.write_text(body)
    print('Extended risk:',len(historical),'historical,',len(forward),'forward portfolios; disclosed holdings are dated proxies')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=ROOT/'config/research.json');p.add_argument('--extensions-config',type=Path,default=ROOT/'config/risk_extensions.json');p.add_argument('--output',type=Path,default=ROOT/'reports/2026-11-06-risk-expansion/risk_extensions.json');p.add_argument('--page',type=Path,default=ROOT/'site/exposure.html');a=p.parse_args();build(a.output,a.page,a.config.resolve(),a.extensions_config.resolve())
