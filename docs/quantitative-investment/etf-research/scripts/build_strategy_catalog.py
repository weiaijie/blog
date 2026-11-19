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
    'allocation': ['2026-11-10-method-gap', '2026-11-14-new-window-attribution'],
    'installments': ['2026-11-10-method-gap'],
    'multifactor_v1': ['2026-11-10-multifactor-shortfall', '2026-11-14-new-window-attribution'],
    'multifactor_adx_v1': ['2026-11-12-adx-shortfall', '2026-11-11-adx-bond'],
}


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
            if technical:
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
    return dict(schemaVersion=1, sourceCommit=SOURCE, evidence=BASE + REPORT, entries=entries)


if __name__ == '__main__':
    path = ROOT / 'site/strategy-catalog.json'
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
