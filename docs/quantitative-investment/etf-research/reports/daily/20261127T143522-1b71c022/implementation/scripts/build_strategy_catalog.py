"""Publish a read-only index of the archived data-version comparison."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'adcf35b37942e5a994c69721df43cf85ce20ce97'
REPORT = 'reports/2026-11-13-data-change/comparison.json'
BASE = 'https://github.com/weiaijie/blog/blob/' + SOURCE + '/docs/quantitative-investment/etf-research/'
VOTES = '沪深300含分红指数高于120日均线、近60日沪深300收益高于国债、沪深300近20日年化波动低于25%，三项至少两票。'
RULES = {
    'allocation': '按设定比例一次建仓，按方案持有或每月再平衡。',
    'installments': '将本金分批按月投入。本报告使用三批，每批按目标配比建仓。',
    'trend_120': '月度观察沪深300含分红指数，高于120日均线则股债各半，否则全债。',
    'multifactor_v1': VOTES,
    'multifactor_volume_v1': VOTES + '另需当日量高于此前20日均量且当日含分红收益为正。',
    'multifactor_kdj_v1': VOTES + '另需KDJ(9,3,3)的K高于D。',
    'multifactor_adx_v1': VOTES + '另需ADX(14)至少25且正向DI高于负向DI。',
}
SPECIAL = {
    'allocation': ['2026-11-10-method-gap', '2026-11-14-new-window-attribution', '2026-11-10-multifactor-shortfall'],
    'installments': ['2026-11-10-method-gap'],
    'multifactor_v1': ['2026-11-10-multifactor-shortfall', '2026-11-14-new-window-attribution'],
    'multifactor_adx_v1': ['2026-11-12-adx-shortfall', '2026-11-11-adx-bond', '2026-11-12-adx-trades'],
}


# Report folders are the immutable experiment identifiers used by the ledger.
EXPERIMENTS = {
    '2026-11-13-data-change': ('新旧数据窗口', '/workbench/#/changes'),
    '2026-11-10-method-gap': ('分批与一次建仓', '/backtest.html#method-gap-case'),
    '2026-11-14-new-window-attribution': ('新增两年窗口归因', '/workbench/#/changes/attribution'),
    '2026-11-10-multifactor-shortfall': ('514个低收益窗口', '/backtest.html#factor-shortfall'),
    '2026-11-12-adx-shortfall': ('321个落后窗口', '/backtest.html#adx-shortfall'),
    '2026-11-11-adx-bond': ('ADX与纯国债', '/backtest.html#adx-bond'),
    '2026-11-12-adx-trades': ('ADX交易与费用', '/backtest.html#adx-trades'),
    '2026-11-11-technical-factors': ('技术因子对照', '/backtest.html#factor-lab'),
}


def relationships(entries):
    from multifactor_strategy import FACTORS

    factors = {item['key']: (item['label'], item['rule']) for item in FACTORS}
    gates = {
        'multifactor_volume_v1': ('volume', '量价确认', '当日量超过此前20日均量且含分红日收益为正'),
        'multifactor_kdj_v1': ('kdj', 'KDJ', 'KDJ(9,3,3) 的 K 高于 D'),
        'multifactor_adx_v1': ('adx', 'ADX', 'ADX(14) ≥ 25 且 +DI > −DI'),
    }
    nodes = []
    edges = []
    for key, (label, rule) in {**factors, **{k: (l, r) for k, l, r in gates.values()}}.items():
        nodes.append(dict(id='factor:' + key, kind='factor', label=label, description=rule))
    experiments = {}
    for entry in entries:
        target = entry['id']
        model = entry['plan']['model']
        nodes.append(dict(id=target, kind='entry', label=entry['label']))
        signals = {}
        if model == 'trend_120':
            signals['trend120'] = '月度择时'
        if model.startswith('multifactor_'):
            signals.update(dict.fromkeys(factors, '三票取二'))
        if model in gates:
            signals[gates[model][0]] = '额外确认'
        for key, role in signals.items():
            edges.append(dict(source='factor:' + key, target=target, role=role))
        for report in entry['reports']:
            folder = report['url'].split('/')[-2]
            experiment = 'experiment:' + folder
            label, view = EXPERIMENTS[folder]
            experiments[experiment] = dict(id=experiment, kind='experiment', label=label,
                                           description=report['title'], url=report['url'], view=view)
            edges.append(dict(source=target, target=experiment, role='对照实验'))
    return dict(version=1, nodes=nodes + list(experiments.values()), edges=edges)


def build():
    raw = (ROOT / REPORT).read_bytes()
    if hashlib.sha256(raw).hexdigest() != '372774685b1236fbbf413509134faf316b9900d5af68292b722852dc2d89e0f4':
        raise ValueError('Unexpected source comparison')
    report = json.loads(raw)
    entries = []
    for row in report['scenarios']:
        model = row['model']
        benchmark = row['group'] == 'markets'
        technical = model in ('multifactor_volume_v1', 'multifactor_kdj_v1', 'multifactor_adx_v1')
        group = '市场基准' if benchmark else '多因子' if model.startswith('multifactor') else '趋势' if model == 'trend_120' else '配置'
        folders = ['2026-11-13-data-change']
        if not benchmark:
            folders.extend(SPECIAL.get(model, []))
            if technical or model == 'multifactor_v1':
                folders.append('2026-11-11-technical-factors')
        reports = []
        for folder in folders:
            path = 'reports/' + folder + '/README.md'
            title = (ROOT / path).read_text(encoding='utf-8').splitlines()[0].lstrip('# ')
            reports.append(dict(title=title, url=BASE + path))
        plan = dict(version=2, dataset='verified-2026-11-12', name=row['label'],
                    start=row['start'], end=report['newThrough'], fees='base', capital=str(report['capital']),
                    model=model, installments='3', portfolios=[row['weights']],
                    rebalance='monthly' if row['rebalance'] == 'monthly' else 'hold')
        rule = RULES[model]
        if model.startswith('multifactor'):
            rule += '满足全部条件时股债各半，否则全债。目标状态改变后次日开盘模拟执行。'
        source = 'technical_factors' if technical else 'multifactor_strategy' if model == 'multifactor_v1' else 'model_replay'
        entries.append(dict(id=row['id'], label=row['label'], group=group, rule=rule,
                            source=BASE + 'scripts/' + source + '.py', reports=reports, plan=plan,
                            periods={year: value['after'] for year, value in row['periods'].items()}))
    return dict(schemaVersion=1, sourceCommit=SOURCE, evidence=BASE + REPORT, entries=entries,
                graph=relationships(entries))


if __name__ == '__main__':
    path = ROOT / 'site/strategy-catalog.json'
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
