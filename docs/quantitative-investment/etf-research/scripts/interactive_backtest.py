"""Read-only user-configured ETF historical simulation, shared by the HTTP API and CLI."""
import argparse
import json
import re
from datetime import date
from decimal import Decimal as D
from fractions import Fraction
from functools import lru_cache
from urllib.parse import parse_qsl

from compare_three_markets import CODES, SCENARIOS, metrics, simulate
from market_evidence import END, START, evidence, verified_inputs

DEFAULTS = dict(start='2024-10-30', end=str(END), capital='100000',
                weights='1,1,1,3', rebalance='monthly', fees='base')
OPTIONS = dict(version=1, method='GET', endpoint='/api/v1/backtest',
               first=str(START), last=str(END), symbols=list(CODES), required=list(DEFAULTS),
               defaults=DEFAULTS, fees=list(SCENARIOS), rebalance=['monthly', 'hold'],
               capitalRange=[1, 1000000000], weightsFormat='Four nonnegative relative amounts in symbols order; up to 2 decimal places each; positive sum.')


class InputError(ValueError):
    pass


def request_params(query):
    try:
        items = parse_qsl(query, keep_blank_values=True, strict_parsing=True, max_num_fields=len(DEFAULTS))
    except ValueError as exc:
        raise InputError('参数格式不正确，或参数过多。') from exc
    params = dict(items)
    if len(items) != len(params) or params.keys() != DEFAULTS.keys():
        raise InputError('请提供 start、end、capital、weights、rebalance、fees 各一次。')
    return params


@lru_cache(maxsize=1)
def inputs():
    return verified_inputs(evidence())


def backtest(params):
    def parse_date(value):
        if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
            raise InputError('日期格式应为 YYYY-MM-DD。')
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise InputError('日期无效。') from exc

    start, end = parse_date(params['start']), parse_date(params['end'])
    if not START <= start < end <= END:
        raise InputError(f'起始日期须早于结束日期，且均在 {START} 至 {END} 之间。')
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

    base, calendar, bars, halts = inputs()
    days = tuple(d for d in calendar if start <= d <= end)
    if len(days) < 2:
        raise InputError('区间至少需要两个已核验交易日。')
    denominators = {s: total/w for s,w in zip(CODES, shares) if w}
    daily, orders = simulate(days, bars, base.dividends, halts, denominators, initial=capital,
                             costs=SCENARIOS[params['fees']], rebalance=params['rebalance'])
    summary = metrics(daily)
    peak = capital
    curve = []
    for row in daily:
        peak = max(peak, row['equity'])
        curve.append(dict(date=row['date'], equity=row['equity'], drawdown=row['equity']/peak-1))
    equity = {r['date']: r['equity'] for r in daily}
    summary.update(ending_equity=daily[-1]['equity'], pnl=daily[-1]['equity']-capital,
                   peak_to_trough_loss=equity[summary['peak']]-equity[summary['trough']],
                   sessions=len(days), filled_orders=sum(order['filled']>0 for order in orders),
                   commissions=sum((order['fee'] for order in orders), D(0)))
    return dict(version=1, parameters=params, symbols=list(CODES), summary=summary, daily=curve, orders=orders)


def encode(result):
    return json.dumps(result, ensure_ascii=False, default=str, allow_nan=False, separators=(',', ':')).encode()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key, default in DEFAULTS.items():
        parser.add_argument('--'+key, default=default)
    args = parser.parse_args()
    try:
        print(encode(backtest(vars(args))).decode())
    except InputError as exc:
        parser.error(str(exc))
