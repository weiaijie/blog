"""Read-only acceptance cases for the dashboard and its Agent API."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ('2026-10-30', '2026-11-12', '2026-11-20', '2026-11-23', '2026-11-26')
API = '/api/v5/backtest'
STANDARD = dict(start='2026-11-23', end='2026-11-26', capital='100000',
                fees='base', weights='1,0,0,1', rebalance='hold')
D = Decimal


def check(base):
    def get(path, params=None, status=200):
        url = base + path + ('?' + urlencode(params) if params else '')
        try:
            request = urlopen(url, timeout=90)
        except HTTPError as exc:
            request = exc
        with request as response:
            if response.status != status:
                raise AssertionError(f'{path}: expected HTTP {status}, got {response.status}')
            return json.load(response)

    def require(test, case):
        if not test:
            raise AssertionError(case)

    options = {}
    for v, through in enumerate(VERSIONS, 1):
        opt = get(f'/api/v{v}/backtest/options')
        require(opt['last'] == through, f'v{v} date drift')
        if v > 1:
            require(opt['dataVersion'] == 'verified-' + through, f'v{v} identity drift')
        options[f'v{v}'] = through

    market = get('/api/v5/market-data')
    coverage = market['coverage']
    require(set(coverage) == {'510300','511010','513500','159920'}, 'Four tickers required')
    for symbol, item in coverage.items():
        bars = market['candles'][symbol]
        dates = [r[0] for r in bars]
        require(dates == sorted(set(dates)) and len(bars) == item['quotes'], f'{symbol}: invalid bars')
        require(item['backtestWindows'][-1][1] == VERSIONS[-1], f'{symbol}: invalid admitted horizon')
    require(len(coverage['513500']['backtestWindows']) == 2, 'S&P split discontinuity')
    require(market['sessions'] == len(market['curve']) and market['asOf'] == market['curve'][-1][0],
            'Forward curve identity')
    invalid = [
        dict(STANDARD, end='2026-11-27'),
        dict(STANDARD, capital='0'),
        dict(STANDARD, weights='0,0,0,0'),
        dict(STANDARD, start='2022-03-28', end='2022-03-31', weights='0,1,0,1'),
    ]
    for params in invalid:
        require('error' in get(API, params, 400), 'Missing input rejection')

    scenarios = {
        'allocation':'hold', 'installments':'hold', 'trend_120':'monthly',
        'multifactor_v1':'signal', 'multifactor_volume_v1':'signal',
        'multifactor_kdj_v1':'signal', 'multifactor_adx_v1':'signal',
    }
    models = {}
    for model, order in scenarios.items():
        args = dict(STANDARD, model=model, rebalance=order)
        if model == 'installments':
            args['installments'] = '3'
        first = get(API+'/replay', dict(args,step='1'))
        all_days = get(API+'/replay', dict(args,step='all'))
        require(first['frames'] == all_days['frames'][:1], f'{model}: first frame depends on run mode')
        require(len(all_days['frames']) == 4 and all_days['frames'][-1]['date'] == '2026-11-26',
                f'{model}: replay date mismatch')
        count = 0
        for frame in all_days['frames']:
            marked = sum(D(frame['bars'][s]['close'])*units for s,units in frame['holdings'].items())
            require(D(frame['equity']) == marked+D(frame['cash'])+D(frame['receivables']),
                    f'{model}: equity reconciliation')
            for fill in frame['orders']:
                require(fill['signal'] < frame['date'] and not fill['filled'] % 100,
                        f'{model}: execution time or lot size')
                count += bool(fill['filled'])
        models[model] = dict(frames=4, fills=count, endingEquity=all_days['frames'][-1]['equity'])

    halts = {}
    for last_day, start in [('2026-11-24','2026-11-23'),('2026-11-25','2026-11-24'),('2026-11-26','2026-11-25')]:
        orders = get(API,dict(STANDARD,start=start,end=last_day,weights='0,1,0,1'))['orders']
        sp = next(o for o in orders if o['symbol']=='513500')
        treasury = next(o for o in orders if o['symbol']=='511010')
        require(treasury['filled'] > 0, 'Treasury leg should execute independently')
        expected = last_day != '2026-11-26'
        require((sp['reason']=='opening_halt' and sp['filled']==0) if expected else sp['filled']>0,
                'Opening halt or primary redemption incorrectly applied')
        halts[last_day] = dict(sp500=sp['filled'],treasury=treasury['filled'],reason=sp['reason'])

    defaults = {}
    for filename, op in [('default-methods.json','method-windows'),('default-technical.json','technical-factors')]:
        saved = json.loads((ROOT/'reports/2026-11-27-admission'/filename).read_bytes())
        result = get(API+'/'+op, saved['parameters'])
        require(result == saved, f'{op} archive differs')
        defaults[op] = {year:next(iter(rows.values()))['count'] for year,rows in result['periods'].items()}

    params = dict(STANDARD,start='2021-10-29',end='2022-11-04',weights='1,0,0,1|0,0,0,1')
    comparison = get(API+'/compare', params)
    detail = get(API+'/overlay', comparison['overlays']['A']['1'])
    a,b = detail['portfolios']
    delta = D(b['summary']['pnl'])-D(a['summary']['pnl'])
    holding = detail['attribution']['holding']['differences']['B-A']['totals']
    gap = detail['attribution']['dailyGaps']['B-A']['days']
    require(delta == D(holding['net']) == sum(D(row['change']) for row in gap) == D(gap[-1]['cumulative']),
            'Daily and full-period PnL differences do not reconcile')
    require(delta == sum(D(holding[k]) for k in ('price','dividend','commission','slippage')),
            'ETF attribution components do not reconcile')

    catalog = get('/strategy-catalog.json')
    graph = catalog['graph']
    ids = {node['id'] for node in graph['nodes']}
    require(len(catalog['entries'])==11 and all(e['source'] in ids and e['target'] in ids for e in graph['edges']),
            'Strategy catalog or graph references are invalid')
    archived = {k:get(p) for k,p in {
        'olderChange':'/api/v2/backtest/data-change',
        'newerChange':'/api/v3/backtest/data-change',
        'newWindowAttribution':'/api/v2/backtest/new-window-attribution',
    }.items()}
    require(len(archived['olderChange']['newSessions'])==9 and len(archived['newerChange']['newSessions'])==6,
            'Archived versions must retain their dated evidence')
    return dict(versions=options, forwardAsOf=market['asOf'], forwardSessions=market['sessions'],
                marketCoverage=coverage, rejectedInputs=len(invalid), replay=models,
                openingOrders=halts, defaultWindowCounts=defaults,
                sameWindow=dict(start=detail['parameters']['start'],end=detail['parameters']['end'],
                                days=len(gap),pnlGap=str(delta),parts=holding),
                catalog=dict(entries=len(catalog['entries']),nodes=len(ids),edges=len(graph['edges'])),
                archiveEndpoints=list(archived))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, help='URL of the internal read-only dashboard')
    args = parser.parse_args()
    print(json.dumps(check(args.base.rstrip('/')),ensure_ascii=False,indent=2))
