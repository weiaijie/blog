"""Collect or replay a dated Shanghai research sample, independent of account admission."""
import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys
from urllib.parse import urlencode
from uuid import uuid4

from collect_market_state_pilot import ROOT, CALENDAR, HOST, query
from market_state_pilot import CODES, amount, equation, financing_detail, result, turnover
from etf_research.admission import completed_date, sessions_between
from etf_research.http_capture import fetch, load_policy, save_transport
from etf_research.policy_events import instant
from etf_research.publication import create, read, seal, sha, verify_bundle

CALENDAR_SHA = '950a3bfe2bab7ad484abc03aa27207bc70a49a4a144f495899cf1bd2aa10c8c6'


def previous_session(day, observed):
    if day > completed_date(observed):
        raise ValueError('Trading day is not complete')
    if sha(CALENDAR) != CALENDAR_SHA:
        raise ValueError('Calendar evidence changed')
    calendar = read(CALENDAR)['holiday_ranges']
    if sessions_between(calendar, day, day) != (day,):
        raise ValueError('Not an exchange session')
    days = sessions_between(calendar, day - timedelta(days=31), day - timedelta(days=1))
    if not days:
        raise ValueError('Previous session unknown')
    return days[-1]


def requests(day, prior):
    key = day.strftime('%Y%m%d')
    return {
        'margin': query('RZRQ_HZ_INFO', prior, day),
        f'market_{key}': HOST + 'commonQuery.do?' + urlencode(dict(
            sqlId='COMMON_SSE_SJ_SCGM_C', TRADE_DATE=day.isoformat(), isPagination='false')),
        f'detail_{key}_1': query('RZRQ_MX_INFO', day, day, 1),
        f'detail_{key}_2': query('RZRQ_MX_INFO', day, day, 2),
    }


def margin_row(folder, day, prior, traded):
    summary = result(folder, 'margin', 'RZRQ_HZ_INFO')
    rows = summary['result']
    by_day = {r['opDate']: r for r in rows}
    key, previous = (d.strftime('%Y%m%d') for d in (day, prior))
    page = summary['pageHelp']
    if (set(by_day) != {key, previous} or len(rows) != 2 or page['pageCount'] != 1
            or page['pageNo'] != 1 or page['total'] != 2 or page['data'] != rows):
        raise ValueError('Incomplete or inconsistent adjacent-session financing summary')
    current = by_day[key]
    detail = financing_detail(folder, key)
    total = amount(current, 'rzmre')
    if sum(amount(row, 'rzmre') for row in detail) != total:
        raise ValueError('Financing detail does not match summary')
    balance = amount(current, 'rzye')
    repayment = amount(current, 'rzche')
    if balance + amount(current, 'rqylje') != amount(current, 'rzrqjyzl'):
        raise ValueError('Combined margin balance does not match its components')
    stocks = [r for r in detail if r['stockCode'][:3] in CODES]
    if not stocks:
        raise ValueError('No same-scope stock detail')
    stock_buy = sum(amount(row, 'rzmre') for row in stocks)
    if traded is not None and stock_buy > traded:
        raise ValueError('Stock financing buys exceed same-scope turnover')
    identity = equation(current, by_day[previous])
    return dict(financingBalanceCny=balance, financingBuyCny=total,
                financingRepaymentCny=repayment, balanceIdentity=identity,
                reconciledFinancingNetCny=total - repayment if identity['status'] == 'matched' else None,
                stockFinancingBuyCny=stock_buy,
                financingBuyShare=str(Decimal(stock_buy) / traded) if traded is not None else None)


def inspect(folder, ready):
    run = read(folder / 'run.json')
    day = date.fromisoformat(run['date'])
    started = instant(run['startedAt'])
    prior = previous_session(day, started)
    if not started <= ready or run['previousDate'] != prior.isoformat() or run['calendarSha256'] != CALENDAR_SHA:
        raise ValueError('Invalid run time or calendar binding')
    expected = requests(day, prior)
    rows = read(folder / 'requests.json')
    if [r['name'] for r in rows] != list(expected):
        raise ValueError('Unexpected request inventory')
    bad = {}
    for row in rows:
        name = row['name']
        file = folder / (name + '.body')
        if (row['url'] != expected[name] or row['sha256'] != sha(file)
                or not started <= instant(row['requested_at_utc']) <= instant(row['receivedAt']) <= ready):
            raise ValueError('Unbound request evidence: ' + name)
        if (row['status'] != 200 or row['curl_exit'] or row.get('error')
                or row['final_url'] != row['url'] or row['metrics']['ssl_verify_result'] != 0):
            bad[name] = f"HTTP {row['status']}, curl {row['curl_exit']}"
    key = day.strftime('%Y%m%d')
    market_name = 'market_' + key
    traded = margin = None
    issues = dict(bad)
    if market_name not in bad:
        try:
            traded = turnover(folder, key)
        except (ValueError, KeyError, TypeError, ArithmeticError) as error:
            issues['turnover'] = str(error)
    if not set(bad) - {market_name}:
        try:
            margin = margin_row(folder, day, prior, traded)
        except (ValueError, KeyError, TypeError, ArithmeticError) as error:
            issues['margin'] = str(error)
    return dict(schemaVersion=1, date=run['date'], previousDate=run['previousDate'],
                scope='SSE A-share and STAR turnover, SSE exchange-wide margin',
                status='full_capture' if not issues else 'partial_capture' if traded or margin else 'blocked',
                historicalPointInTime=False, researchOnly=True,
                receivedAt=max((instant(row['receivedAt']) for row in rows)).isoformat(),
                featureReadyAt=ready.isoformat() if traded or margin else None,
                checkedAt=ready.isoformat(), publishedAt=None,
                turnoverCny=format(traded, 'f') if traded is not None else None,
                margin=margin, relativeTurnover20=None, breadth=None, issues=issues)


def collect(day, parent):
    started = datetime.now(timezone.utc)
    prior = previous_session(day, started)
    folder = parent / (started.strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8] + '-sse-research-day')
    folder.mkdir(parents=True, exist_ok=False)
    policy = load_policy()
    save_transport(folder, policy)
    create(folder / 'run.json', dict(date=str(day), previousDate=str(prior), startedAt=started.isoformat(),
                                     calendarSha256=CALENDAR_SHA))
    rows = []
    for name, url in requests(day, prior).items():
        response = fetch(folder, name, url, policy)
        response['receivedAt'] = datetime.now(timezone.utc).isoformat()
        rows.append(response)
    create(folder / 'requests.json', rows)
    summary = inspect(folder, datetime.now(timezone.utc))
    create(folder / 'result.json', summary)
    seal(folder)
    return folder, verify(folder)


def verify(folder):
    verify_bundle(folder)
    saved = read(folder / 'result.json')
    if saved != inspect(folder, instant(saved['checkedAt'])):
        raise ValueError('Dated observation does not reproduce')
    return saved


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--day', type=date.fromisoformat)
    action.add_argument('--verify', type=Path)
    parser.add_argument('--output-parent', type=Path, default=ROOT / 'data/snapshots')
    options = parser.parse_args()
    folder, evidence = ((options.verify, verify(options.verify)) if options.verify
                        else collect(options.day, options.output_parent))
    print(f"{folder}: {evidence['status']}; {evidence['issues']}")
