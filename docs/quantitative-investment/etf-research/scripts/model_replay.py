"""Chronological replay of verified ETF bars for the workbench and its read-only API."""
from collections import defaultdict
from dataclasses import replace
from decimal import Decimal as D
import re

import interactive_backtest as work
from compare_three_markets import allocation_targets
from etf_research.baselines import run, targets, trend_weights
from etf_research.signal_audit import signal_weights


def replay(params):
    config = {key: params[key] for key in work.DEFAULTS}
    model, step = params['model'], params['step']
    installments = params.get('installments', '3')
    if model == 'installments':
        if not re.fullmatch(r'[2-9]|1[0-2]', installments):
            raise work.InputError('建仓期数须为 2 至 12 的整数。')
        config['installments'] = installments
    elif 'installments' in params:
        raise work.InputError('只有分批建仓可以设置期数。')
    if model not in ('allocation', 'trend_120', 'installments'):
        raise work.InputError('请选择固定配比、分批建仓或 120 日趋势模型。')
    if model == 'trend_120' and (config['weights'] != '1,0,0,1' or config['rebalance'] != 'monthly'):
        raise work.InputError('冻结趋势模型使用月度调仓，配比参数须为 1,0,0,1。')
    days, capital, simulate = work.configured_replay(config)
    if step != 'all' and (not re.fullmatch('[1-9][0-9]{0,3}', step) or int(step) > len(days)):
        raise work.InputError(f'回放步数应为 1 至 {len(days)} 或 all。')
    visible = days if step == 'all' else days[:int(step)]
    base, _, bars, _ = work.inputs()
    symbols = list(simulate.keywords['denominators'])
    orders = defaultdict(list)
    schedule = None
    if model == 'trend_120':
        if base.sessions.index(days[0]) < 120:
            raise work.InputError(f'趋势模型需要起点前已有 120 个收盘，最早起点为 {base.sessions[120]}。')
        sessions = tuple(d for d in base.sessions if d <= visible[-1])
        data = replace(base, sessions=sessions,
                       bars={s: {d: base.bars[s][d] for d in sessions} for s in symbols},
                       dividends=tuple(e for e in base.dividends if e.announcement_date <= visible[-1]))
        closes = [(d, data.bars['510300'][d].close) for d in sessions]
        result = run(data, model, config['fees'], capital, account_start=days[0])
        daily = result['daily']
        trades = {(r['day'], r['symbol'], r['side']): r for r in result['journal'] if r['kind'] == 'trade'}
        for order in result['decisions']:
            trade = trades.get((order['day'], order['symbol'], order['side']), {})
            orders[order['day']].append(dict(signal=order['signal_date'], symbol=order['symbol'], side=order['side'],
                requested=order['requested_units'], filled=order['filled_units'], target=order['target_units'],
                price=trade.get('fill_price'), fee=trade.get('commission', D(0)), reason=order['reason']))
        # The next scheduled session is calendar information. No price for it is supplied.
        if len(visible) < len(days):
            data = replace(data, sessions=sessions+(days[len(visible)],))
    else:
        available = {s: {d: bars[s][d] for d in visible} for s in symbols}
        if model == 'installments':
            from installment_strategy import installment_schedule
            schedule = installment_schedule(days, visible, available[symbols[0]], int(installments),
                                            config['rebalance'], simulate.keywords['denominators'])
        daily, executions = simulate(visible, bars=available, schedule=schedule,
            events=tuple(e for e in base.dividends if e.announcement_date <= visible[-1]))
        for order in executions:
            orders[order['day']].append(dict(signal=order['signal'], symbol=order['symbol'], side=order['side'],
                requested=order['requested'], filled=order['filled'], target=order['target'],
                price=order['modeled_price'] if order['filled'] else None, fee=order['fee'], reason=order['reason']))

    frames = []
    peak = previous = capital
    for i, row in enumerate(daily):
        day, equity = row['date'], row['equity']
        quotes = {s: {key: getattr(bars[s][day], key) for key in ('open', 'high', 'low', 'close')} for s in symbols}
        next_day = days[i+1] if i+1 < len(days) else None
        plan = None
        due = next_day and (i == 0 or (config['rebalance']=='monthly' and next_day.month != day.month))
        if (next_day in schedule if schedule is not None else due):
            marks = {s: q['close'] for s,q in quotes.items()}
            if model == 'trend_120':
                weights = trend_weights(data, next_day)
                checked, spread = signal_weights(model, closes, data.dividends, day)
                if checked != (weights['510300'], weights['511010']):
                    raise ValueError('Trend explanation disagrees with frozen decision')
                units = targets(weights, equity, marks)
                reason = 'trend_on' if weights['510300'] else 'trend_off'
            elif schedule is not None:
                entry = schedule[next_day]
                units = allocation_targets(entry['denominators'], equity, marks)
                reason = entry['reason']
            else:
                units = allocation_targets(simulate.keywords['denominators'], equity, marks)
                reason = 'initial' if i == 0 else 'monthly'
            plan = dict(signal=day, execution=next_day, reason=reason, target=units,
                        change={s:n-row['units_'+s] for s,n in units.items()})
            if model == 'trend_120':
                plan['trendSpread'] = spread
            if schedule is not None:
                plan.update(batch=entry['batch'], installments=entry['installments'])
        peak = max(peak, equity)
        frames.append(dict(date=day, bars=quotes, holdings={s:row['units_'+s] for s in symbols},
            equity=equity, cash=row['cash'], availableCash=row['available_cash'], receivables=row['receivables'],
            dayPnl=equity-previous, pnl=equity-capital, drawdown=equity/peak-1,
            orders=orders[day], nextPlan=plan))
        previous=equity
    return dict(model=model, parameters=config, totalSessions=len(days), step=len(frames), frames=frames)
