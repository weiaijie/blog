"""Generate immutable history and prospective reports alongside the daily accounts."""
import csv, html, json, sys
from pathlib import Path
from datetime import date
from decimal import Decimal as D
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.monthly import index_levels, compare
from etf_research.publication import read, create, sha
from etf_research.long_history import load_long_history


def build(folder, current, state, history_results):
    policy_path = ROOT/'config/monthly_benchmark.json'
    cfg = read(policy_path)
    create(folder/'monthly_policy.json', cfg)
    calendar = read(ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json')['holiday_ranges']
    historic = load_long_history(ROOT/'data/snapshots')
    sources = list(read(history_results)['results'])
    history = {}
    for r in sources:
        path = history_results.parent/(r['run']+'_daily.csv')
        with path.open() as f:
            history[r['run']] = list(csv.DictReader(f))
    report = dict(policy_sha256=sha(policy_path), checkpoint_sha256=state['checkpoint_sha256'])
    main = {}
    for scope, data, accounts in [('history', historic, history),
            ('forward', current, {s: p['daily'] for s, p in state['portfolios'].items()})]:
        first = next(iter(accounts.values()))
        days = [date.fromisoformat(r['date']) for r in first]
        levels = index_levels(data, days, cfg)
        report[scope] = {}
        for account, records in accounts.items():
            if [r['date'] for r in records] != [r['date'] for r in first]:
                raise ValueError('Inconsistent account dates')
            rows = compare(days, [D(r['equity']) for r in records], levels, calendar, cfg)
            report[scope][account] = rows
        main[scope] = report[scope]['monthly_50_50_base_100000_d1' if scope=='history' else 'monthly_50_50_base']
    create(folder/'monthly.json', report)
    body = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>股债基准与月报</title><link rel="stylesheet" href="style.css"><main><a href="index.html">返回日报</a><h1>股债基准与月报</h1><p>主观察组合：50/50、基准费用。对照序列从各自首个收盘起算；510300 与 511010 各半，跨月前收盘再平衡，官方现金分红在除息收盘按零碎份额再投资，不计费用。它是 ETF 总收益代理，并非官方指数。组合净收益包含冻结模型费用。</p>']
    for scope, title in [('forward','前瞻模拟'),('history','独立历史研究')]:
        body.append(f'<section><h2>{title}</h2><div class="table-wrap"><table><thead><tr><th>月份 / 状态</th><th>收益日</th><th>组合净收益</th><th>基准收益</th><th>相对收益（百分点）</th><th>月内最大回撤</th><th>年化跟踪误差</th></tr></thead><tbody>')
        for row in reversed(main[scope]):
            cells = [row['month'] + (' 完整' if row['complete'] else ' 部分月'), str(row['paired_returns'])]
            for k in ('net_return','benchmark_return','relative_return','max_drawdown','tracking_error_annualized'):
                v = row[k]
                cells.append('样本不足' if v is None else (f'{100*v:.3f}' if k=='relative_return' else f'{v:.3%}'))
            body.append('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in cells)+'</tr>')
        body.append('</tbody></table></div></section>')
    body.append('<p>相对收益是同期收益之差。完整月需有上月末收盘锚和当月全部交易日。部分月仅列已观察区间；跟踪误差为完整月至少10个配对日收益差的样本标准差乘以√252。历史与前瞻独立起算，不能拼接。</p><nav><a href="../monthly.json">全部组合月报与累计收益</a><a href="../monthly_policy.json">固定基准口径</a></nav></main></html>')
    (folder/'site/monthly.html').write_text(''.join(body), encoding='utf-8')
