"""Compare the November 12 and 20 sealed cohorts; expose the same report to HTTP and CLI."""
import argparse
from datetime import date
from decimal import Decimal
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import data_change_report as change
import november_market_data as latest
import recent_backtest as api
from build_entry_windows import entry_schedule
from recent_market_data import THROUGH as PRIOR_END
from research_profile import LATEST, RECENT, using

END = latest.THROUGH
REPORT = change.REPORT.parent / '2026-11-23-six-session-change'
SHA256 = '389d259856c3804f048317445a2ec178b96be634a98b2dda4fca7d07ddc34480'
METRICS = ('count', 'profitable', 'reached', 'worstPnl', 'worstStart', 'worstEnd')


def check_metrics(a, b):
    for key in METRICS:
        pair = a[key], b[key]
        if key == 'worstPnl':
            pair = tuple(Decimal(str(x)) for x in pair)
        if pair[0] != pair[1]:
            raise ValueError(f'Metric mismatch {key}: {pair}')


def old_rows(scenario, days, domestic, previous):
    if scenario['group'] == 'domestic':
        rows = list(domestic[scenario['model']])
        for period in previous['periods'].values():
            for w in period['newWindows']:
                rows.append(change.measure(date.fromisoformat(w['start']), date.fromisoformat(w['end']),
                                           w['years'], w['ending_equity']))
        return rows
    rows = []
    with using(RECENT):
        for sessions, ends in entry_schedule(days):
            ledger, _ = change.cross_book(scenario, sessions[0], sessions[-1])
            for years, i in ends.items():
                rows.append(change.measure(sessions[0], sessions[i], years, ledger[i]['equity']))
    return rows


def relaxed_book(scenario, start, end):
    return change.cross_book(scenario, start, end, True, prior_end=PRIOR_END, through=END)


def paired_controls(scenario, days, halt_days, cases):
    # Monthly execution can only fall on session 2 of the account or on a month boundary.
    # All three halts are mid-month. Enumerate every eligible initial order for this scenario.
    controls = []
    for halt in halt_days:
        start = days[days.index(halt)-1]
        if start.month != halt.month:
            raise ValueError('Month boundary requires scanning all open accounts')
        ledger, orders = change.cross_book(scenario, start, END)
        relaxed, hypothetical = relaxed_book(scenario, start, END)
        blocked = [o for o in orders if o['reason'] == 'opening_halt' and o['day'] == halt]
        if not blocked:
            continue
        if len(blocked) != 1 or blocked[0]['symbol'] != '513500' or blocked[0]['filled']:
            raise ValueError('Unexpected opening halt order')
        case = f"{scenario['id']}-initial-{halt}"
        cases[case] = dict(id=case, scenario=scenario['id'], start=str(start), end=str(END),
                           years=0, kind='diagnostic', dataVersion=LATEST)
        controls.append(dict(case=case, scenario=scenario['id'], label=scenario['label'], order=blocked[0],
                             actualOrders=[o for o in orders if o['day'] == halt],
                             diagnosticOrders=[o for o in hypothetical if o['day'] == halt],
                             closeEffect=ledger[1]['equity']-relaxed[1]['equity'],
                             endingEffect=ledger[-1]['equity']-relaxed[-1]['equity']))
    return controls


def build():
    previous = {s['id']: s for s in change.report()['scenarios']}
    (base, calendar, _, _), audit, _ = latest.admitted()
    domestic = change.old_domestic()
    cases, scenarios, controls = {}, [], []
    halt_days = [date.fromisoformat(d) for d in audit['openingHalts']]
    for scenario in change.SCENARIOS.values():
        sid = scenario['id']
        home = scenario['group'] == 'domestic'
        days = tuple(d for d in (base.sessions if home else calendar) if str(d) >= scenario['start'])
        baseline = old_rows(scenario, tuple(d for d in days if d <= PRIOR_END), domestic, previous[sid])
        old_keys = {(r['start'], r['end'], r['years']) for r in baseline}
        schedule = [(s[0], s[i], y) for s, ends in entry_schedule(days) for y, i in ends.items()]
        if old_keys != {k for k in schedule if k[1] <= PRIOR_END}:
            raise ValueError('Old maturity dates changed')
        actual, relaxed, details = [], [], []
        with using(LATEST):
            for start, end, years in schedule:
                if end <= PRIOR_END:
                    continue
                if home:
                    book = change.model_replay.replay(change.replay_params(scenario, start, end))
                    equity = diagnostic = book['frames'][-1]['equity']
                    blocked = []
                else:
                    ledger, orders = change.cross_book(scenario, start, end)
                    other, _ = relaxed_book(scenario, start, end)
                    equity, diagnostic = ledger[-1]['equity'], other[-1]['equity']
                    blocked = [o for o in orders if o['day'] in halt_days and o['reason'] == 'opening_halt']
                row = change.measure(start, end, years, equity)
                actual.append(row)
                relaxed.append(change.measure(start, end, years, diagnostic))
                key = f'{sid}-{years}-new-{start}'
                cases[key] = dict(id=key, scenario=sid, start=str(start), end=str(end), years=years,
                                  kind='new', dataVersion=LATEST)
                details.append(dict(row, case=key, blockedOrders=len(blocked), orders=blocked,
                                    haltEffectPnl=equity-diagnostic))
            if not home:
                controls.extend(paired_controls(scenario, days, halt_days, cases))
        periods = {}
        for year in (1, 2):
            old = [r for r in baseline if r['years'] == year]
            new = [r for r in actual if r['years'] == year]
            alt = [r for r in relaxed if r['years'] == year]
            result = change.compare_cohorts(old, old+new, old+alt)
            check_metrics(result['before'], previous[sid]['periods'][str(year)]['after'])
            if home:
                op, defaults = ('method-windows', change.method_windows.DEFAULTS) if scenario['model'] in change.method_windows.MODELS else ('technical-factors', change.factor_lab.DEFAULTS)
                full = api.calculate(op, dict(defaults, end=str(END)), LATEST)
                check_metrics(result['after'], full['periods'][str(year)][scenario['model']])
            for side, profile in [('before', RECENT), ('after', LATEST)]:
                metric = result[side]
                key = f'{sid}-{year}-worst-{side}'
                cases[key] = dict(id=key, scenario=sid, start=metric['worstStart'], end=metric['worstEnd'],
                                  years=year, kind='worst-'+side, dataVersion=profile)
                metric['worstCase'] = key
            result['newWindows'] = [r for r in details if r['years'] == year]
            periods[year] = result
        scenarios.append(dict(scenario, periods=periods, newHaltBlockedOrders=sum(w['blockedOrders'] for w in details)))
    return dict(schemaVersion=2, oldThrough=str(PRIOR_END), newThrough=str(END), newSessions=audit['addedSessions'],
                capital=str(change.CAPITAL), fees='base', annualTarget='0.04', scenarios=scenarios, cases=cases,
                openingHalts=audit['openingHalts'], controls=controls,
                haltNotices=[n for n in audit['notices'] if n['kind']=='opening_halt_until_10:30'],
                notes=['七个境内模型从2019-03-20起算，四组月度股债基准从2022-03-30起算。每期从10万元现金开始，股票初始目标50%，其余为国债，模型信号可改变仓位。',
                       '按人民币净盈亏计数，含已核验分红，单边佣金万三、最低5元，滑点5个基点。周年到期遇休市顺延至首个可用交易日。',
                       '新旧差额分为新增到期样本与停牌规则两部分。相邻起点重叠，次数不能直接解读为独立成功概率。',
                       '条件差额为按公告阻断的期末权益减去仅放开这三次限制并按日线开盘价模拟的权益。真实可成交价及复牌后的可成交量未知。'])


@lru_cache(maxsize=1)
def report():
    latest.admitted()
    body = (REPORT/'comparison.json').read_bytes()
    if hashlib.sha256(body).hexdigest() != SHA256:
        raise ValueError('November version comparison digest differs')
    return json.loads(body)


def detail(query):
    return change.case_detail(query, report(), PRIOR_END, END)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--output', type=Path, help='Write a newly computed report to a new file')
    group.add_argument('--case')
    args = parser.parse_args()
    if args.output:
        body = change.work.encode(build())
        with args.output.open('xb') as stream:
            stream.write(body)
        print(hashlib.sha256(body).hexdigest())
    else:
        print(change.work.encode(detail({'case':args.case}) if args.case else report()).decode())
