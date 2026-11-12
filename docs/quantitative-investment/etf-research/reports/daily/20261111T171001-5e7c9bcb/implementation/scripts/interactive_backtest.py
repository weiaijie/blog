"""Read-only user-configured ETF historical simulation, shared by the HTTP API and CLI."""
import argparse
import json
import re
from datetime import date
from decimal import Decimal as D
from fractions import Fraction
from functools import lru_cache, partial
from urllib.parse import parse_qsl

import multifactor_strategy as multi
from compare_three_markets import CODES, SCENARIOS, metrics, simulate
from build_entry_windows import entry_schedule, measure_entry, summarize
from overlay_attribution import attribution, cumulative_ledger
from etf_research.long_history import START as DOMESTIC_START
from market_events_2022 import RESUMED, SPLIT_DAY
from market_evidence import END, EXTENDED_START, evidence, verified_inputs

DEFAULTS = dict(start=str(RESUMED), end=str(END), capital='100000',
                weights='1,1,1,3', rebalance='monthly', fees='base')
OPTIONS = dict(version=1, method='GET', endpoint='/api/v1/backtest',
               replayEndpoint='/api/v1/backtest/replay', replayModels=['allocation','installments','trend_120',multi.MODEL],
               multifactorV1=dict(model=multi.MODEL, weights='1,0,0,1', rebalance='signal', requiredVotes=2,
                                  factors=multi.FACTORS, frequency='daily close; execute next open on initial or switch'),
               replayInstallments=dict(min=2,max=12,default=3), replayStep='1..totalSessions or all',
               windowsEndpoint='/api/v1/backtest/windows', compareEndpoint='/api/v1/backtest/compare',
               overlayEndpoint='/api/v1/backtest/overlay',
               compareWeightsFormat='2 or 3 four-ETF relative weight vectors, in input order, separated by |', horizons=[1, 2], annualTarget='0.04',
               first=str(RESUMED), overseasFirst=str(EXTENDED_START), splitDay=str(SPLIT_DAY),
               preSplitLast='2022-03-28', trendFirst='2019-03-20', domesticFirst=str(DOMESTIC_START), last=str(END), symbols=list(CODES), required=list(DEFAULTS),
               defaults=DEFAULTS, fees=list(SCENARIOS), rebalance=['monthly', 'hold'],
               capitalRange=[1, 1000000000], weightsFormat='Four nonnegative relative amounts in symbols order; up to 2 decimal places each; positive sum.')


class InputError(ValueError):
    pass


def request_params(query, keys=DEFAULTS, optional=()):
    try:
        items = parse_qsl(query, keep_blank_values=True, strict_parsing=True, max_num_fields=len(keys)+len(optional))
    except ValueError as exc:
        raise InputError('参数格式不正确，或参数过多。') from exc
    params = dict(items)
    if len(items) != len(params) or not set(keys) <= params.keys() <= set(keys).union(optional):
        raise InputError('请各提供一次参数：' + '、'.join(keys))
    return params


@lru_cache(maxsize=1)
def inputs():
    return verified_inputs(evidence(), extended=True)


def configured_replay(params):
    def parse_date(value):
        if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
            raise InputError('日期格式应为 YYYY-MM-DD。')
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise InputError('日期无效。') from exc

    start, end = parse_date(params['start']), parse_date(params['end'])
    if not re.fullmatch(r'[0-9]{1,10}(\.[0-9]{1,2})?', params['capital']):
        raise InputError('本金应为人民币金额，最多两位小数。')
    capital = D(params['capital'])
    if not 1 <= capital <= 1000000000:
        raise InputError('本金范围为 1 至 10 亿元。')
    parts = params['weights'].split(',')
    if len(parts) != len(CODES) or any(not re.fullmatch(r'[0-9]{1,5}(\.[0-9]{1,2})?', p) for p in parts):
        raise InputError('请填写四个非负配比，每项最多五位整数、两位小数。')
    shares = list(map(Fraction, parts))
    total = sum(shares)
    if not total:
        raise InputError('至少一只 ETF 的配比须大于零。')
    if params['fees'] not in SCENARIOS or params['rebalance'] not in OPTIONS['rebalance']:
        raise InputError('费用或调仓选项无效。')

    domestic_only = not (shares[1] or shares[2])
    first = DOMESTIC_START if domestic_only else EXTENDED_START
    if not first <= start < end <= END:
        raise InputError(f'按所选配比，可用区间为 {first} 至 {END}，起始日期须早于结束日期。')
    if shares[1] and start <= SPLIT_DAY <= end:
        raise InputError('标普 ETF 于 2022-03-29 拆分停牌，无场内收盘价。请选择截至 2022-03-28 或自 2022-03-30 起的区间。')
    base, common_calendar, bars, halts = inputs()
    calendar = base.sessions if domestic_only else common_calendar
    days = tuple(d for d in calendar if start <= d <= end)
    if len(days) < 2:
        raise InputError('区间至少需要两个已核验交易日。')
    denominators = {s: total/w for s,w in zip(CODES, shares) if w}
    replay = partial(simulate, bars=bars, events=base.dividends, halts=halts, denominators=denominators,
                     initial=capital, costs=SCENARIOS[params['fees']], rebalance=params['rebalance'])
    return days, capital, replay


def backtest(params):
    days, capital, replay = configured_replay(params)
    return account_report(params, capital, *replay(days))


def account_report(params, capital, daily, orders):
    summary = metrics(daily)
    peak = capital
    curve = []
    for row in daily:
        peak = max(peak, row['equity'])
        curve.append(dict(date=row['date'], equity=row['equity'], drawdown=row['equity']/peak-1))
    equity = {r['date']: r['equity'] for r in daily}
    summary.update(ending_equity=daily[-1]['equity'], pnl=daily[-1]['equity']-capital,
                   peak_to_trough_loss=equity[summary['peak']]-equity[summary['trough']],
                   sessions=len(daily), filled_orders=sum(order['filled']>0 for order in orders),
                   commissions=sum((order['fee'] for order in orders), D(0)))
    return dict(version=1, parameters=params, symbols=list(CODES), summary=summary, daily=curve, orders=orders)


def entry_windows(params):
    return window_report(params, *configured_replay(params))


def window_report(params, days, capital, replay):
    cohorts = {1: [], 2: []}
    for sessions, endpoints in entry_schedule(days):
        ledger, _ = replay(sessions)
        for row in measure_entry(ledger, endpoints, capital):
            cohorts[row['years']].append(row)

    periods = {}
    for years, rows in cohorts.items():
        if not rows:
            periods[years] = dict(count=0, profitable=0, reached=0, worstReplay=None)
            continue
        stats = summarize(rows)
        worst = backtest(dict(params, start=stats['worstStart'], end=stats['worstEnd']))
        if worst['summary']['pnl'] != min(r['pnl'] for r in rows):
            raise ValueError('Worst window failed endpoint reconciliation')
        periods[years] = dict(**stats, firstStart=rows[0]['start'], lastStart=rows[-1]['start'],
                              worstReplay=worst)
    return dict(version=1, parameters=params, symbols=list(CODES), annualTarget='0.04',
                firstSession=days[0], lastSession=days[-1], periods=periods)


def comparison_inputs(params):
    vectors = params['weights'].split('|')
    if len(vectors) not in (2, 3):
        raise InputError('请提供两套或三套配比，用 | 分隔。')
    prepared = []
    for label, weights in zip('ABC', vectors):
        portfolio = dict(params, weights=weights)
        try:
            config = configured_replay(portfolio)
        except InputError as exc:
            raise InputError(f'组合 {label}：{exc}') from exc
        prepared.append((label, portfolio, config))
    return prepared


def compare_windows(params):
    reports = [dict(id=label, **window_report(portfolio, *config))
               for label, portfolio, config in comparison_inputs(params)]
    # Each link takes the chosen maturity's dates and the entire comparison's weights.
    overlays = {p['id']: {y: dict(params, start=s['worstStart'], end=s['worstEnd']) if s['count'] else None
                          for y, s in p['periods'].items()} for p in reports}
    return dict(version=1, parameters=params, symbols=list(CODES), portfolios=reports, overlays=overlays)


def same_window(params):
    portfolios = []
    ledgers = {}
    base, _, bars, _ = inputs()
    for label, portfolio, (days, capital, replay) in comparison_inputs(params):
        daily, orders = replay(days)
        account = account_report(portfolio, capital, daily, orders)
        ledgers[label] = cumulative_ledger(daily, orders, bars, base.dividends)
        summary = account['summary']
        if summary['max_drawdown'] == 0:
            state = 'no_drawdown'
        elif summary['recovery'] is None:
            state = 'unrecovered'
        else:
            state = 'recovered'
        curve = [dict(**row, nav=row['equity']/capital) for row in account['daily']]
        portfolios.append(dict(id=label, weights=portfolio['weights'], summary=summary, daily=curve,
                               recoveryState=state))
    best_pnl = max(p['summary']['pnl'] for p in portfolios)
    shallowest = max(p['summary']['max_drawdown'] for p in portfolios)
    recovered = [p for p in portfolios if p['recoveryState'] == 'recovered']
    earliest = min((p['summary']['recovery'] for p in recovered), default=None)
    leaders = dict(highestPnl=[p['id'] for p in portfolios if p['summary']['pnl']==best_pnl],
                   shallowestDrawdown=[p['id'] for p in portfolios if p['summary']['max_drawdown']==shallowest],
                   firstRecovery=[p['id'] for p in recovered if p['summary']['recovery']==earliest])
    return dict(version=1, parameters=params, symbols=list(CODES), portfolios=portfolios, leaders=leaders,
                attribution=attribution(ledgers,portfolios))


def encode(result):
    return json.dumps(result, ensure_ascii=False, default=str, allow_nan=False, separators=(',', ':')).encode()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key, default in DEFAULTS.items():
        parser.add_argument('--'+key, default=default)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--compare', action='store_true', help='Compare 2 or 3 weight vectors separated by |')
    modes.add_argument('--windows', action='store_true', help='Scan all mature one- and two-year entries')
    modes.add_argument('--overlay', action='store_true', help='Replay all portfolios on the same dates')
    args = vars(parser.parse_args())
    overlay = args.pop('overlay')
    comparison = args.pop('compare')
    calculate = entry_windows if args.pop('windows') else backtest
    if comparison:
        calculate = compare_windows
    if overlay:
        calculate = same_window
    try:
        print(encode(calculate(args)).decode())
    except InputError as exc:
        parser.error(str(exc))
