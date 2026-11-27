"""Observe actual calls in a read-only frozen replay, compare to the independent files."""
import argparse
import csv
from collections import Counter, defaultdict
from contextlib import ExitStack
from decimal import Decimal as D, localcontext
import hashlib
import json
from unittest.mock import patch

from build_signal_audit import CASES, MATRIX, PLAN, ROOT, SNAP, SYMS, Path, load_long_history, read, save, sha
from etf_research import baselines as frozen
from etf_research.forward import digest


def records(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def audit(folder):
    differences, counts = [], Counter()
    def check(run, key, actual, expected):
        counts[key] += 1
        if actual != expected:
            differences.append(dict(run=run, field=key, reconstructed=actual, reference=expected))

    for name, expected in read(folder/'inputs.json').items():
        check(name,'source_hash',sha(ROOT/name),expected)
    data = load_long_history(SNAP)
    # Independent full-history index; rescale the spread to the first level of each window.
    levels, spreads = [], {}
    ex = {e.ex_date:e for e in data.dividends if e.symbol == SYMS[0]}
    with localcontext() as ctx:
        ctx.prec = 75
        for i,d in enumerate(data.sessions):
            bar = data.bars[SYMS[0]][d]
            cash = ex[d].per_share if d in ex and ex[d].announcement_date <= d else 0
            levels.append(levels[-1] * (bar.close + cash) / prev if i else D(1))
            prev = bar.close
            if i >= 119:
                spreads[str(d)] = (levels[-1] - sum(levels[-120:])/120) / levels[-120]
    sealed = {r['run']:r for r in read(MATRIX)['cases']}
    target_rows = defaultdict(list)
    for row in records(folder/'targets.csv'):
        target_rows[row['run']].append(row)
    cases = records(folder/'cases.csv')
    names = [f'{s}_{f}_{c}_d{d}' for s,f,c,d in CASES]
    check('all','case_coverage',sorted(target_rows),sorted(names))
    check('all','case_order',[r['run'] for r in cases],names)
    check('all','matrix_coverage',sorted(sealed),sorted(n.replace('_d','_') for n in names))
    original_target, original_open = frozen.targets, frozen.Ledger.open_session
    totals = Counter()
    for (s, fee, capital, delay), name, case in zip(CASES,names,cases):
        generated, waiting = [], []
        def observe_target(weights,equity,marks):
            ret = original_target(weights,equity,marks)
            waiting.append((equity, tuple(marks[k] for k in SYMS), tuple(weights[k] for k in SYMS), tuple(ret[k] for k in SYMS)))
            return ret
        def observe_open(ledger,day):
            generated.extend((str(day), *x) for x in waiting)
            waiting.clear()
            return original_open(ledger,day)
        with ExitStack() as stack:
            stack.enter_context(patch.object(frozen, 'targets', observe_target))
            stack.enter_context(patch.object(frozen.Ledger, 'open_session', observe_open))
            replay = frozen.run(data,s,fee,D(capital),execution_delay=delay)
        rows = target_rows[name]
        check(name,'batch_count',(len(rows), int(case['batches'])), (len(generated),len(generated)))
        check(name,'terminal_nav',D(case['terminal_nav']),D(replay['summary']['ending_equity']))
        check(name,'pending',sum(not row['execution_day'] for row in rows),replay['summary']['pending_target_batches_at_end'])
        expected, observed = {}, {}
        for record in replay['decisions']:
            d = str(record['day'])
            observed.setdefault(d,[]).append((record['symbol'],record['target_units'],str(record['signal_date'])))
        close_rows = {str(d['date']):d for d in replay['daily']}
        pos = {str(d):i for i,d in enumerate(data.sessions)}
        for row, ref in zip(rows,generated):
            key = name+'/'+row['signal_date']
            nxt, nav, marks, weights, units = ref
            target = tuple(int(row[k+'_target']) for k in ('stock','bond'))
            check(key,'signal_inputs_and_targets',(row['next_session'],D(row['signal_nav']),
                tuple(D(row[k+'_close']) for k in ('stock','bond')),
                tuple(D(row[k+'_weight']) for k in ('stock','bond')),target), ref)
            i = pos[nxt]
            signal = str(data.sessions[i-1])
            if s == 'trend_120':
                check(key,'trend_spread_within_1e-45',abs(D(row['trend_spread'])-spreads[signal]) <= D('1e-45'),True)
            else:
                check(key,'non_trend_spread',row['trend_spread'],'')
            j = i + delay - 1
            day = str(data.sessions[j]) if j < len(data.sessions) else ''
            check(key,'calendar',(row['signal_date'],row['execution_day'],int(row['delay'])),(signal,day,delay))
            if not day:
                check(key,'pending_row',row['state'],'pending')
                continue
            prior = close_rows[str(data.sessions[j-1])]
            pre = tuple(prior['units_'+sym] for sym in SYMS)
            check(key,'prior_units',tuple(int(row[k+'_before']) for k in ('stock','bond')),pre)
            changes = list(zip(SYMS,target,pre))
            plan = [(sym,n,signal) for direction in (-1,1) for sym,n,old in changes if direction*(n-old)>0]
            state = 'decision' if plan else 'unchanged'
            check(key,'batch_state',row['state'],state)
            totals[state] += 1
            if plan:
                expected[day] = plan
        check(name,'decision_path',expected,observed)
        legacy = sealed[name.replace('_d','_')]
        schedule_hash = hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()
        check(name,'sealed_target_schedule',schedule_hash,legacy['target_schedule_sha256'])
        totals['decision_lines'] += sum(map(len,observed.values()))
        totals['batches'] += len(rows)
    blind, plan = read(folder/'forward.json'), read(PLAN)
    check('forward','plan_checksum',digest({k:v for k,v in plan.items() if k!='plan_sha256'}),plan['plan_sha256'])
    for k in ('source_through','target_session','previous_closes'):
        check('forward',k,blind[k],plan[k])
    check('forward','prior_checkpoint',blind['prior_checkpoint_sha256'],plan['checkpoint_sha256'])
    check('forward','accounts',sorted(blind['portfolios']),sorted(plan['portfolios']))
    for name, row in blind['portfolios'].items():
        other = plan['portfolios'][name]
        for k in ('weights','signal_date','target_units','previous_holdings','previous_equity'):
            check(name,'forward_'+k,row[k],other[k])
    return dict(scope='signal and target reconstruction conditional on sealed past fills',
                sessions=len(data.sessions), cases=len(cases), forward_accounts=len(blind['portfolios']),
                **totals, checks=dict(counts), comparison_inputs={p.relative_to(ROOT).as_posix():sha(p) for p in (PLAN,MATRIX)},
                difference_count=len(differences), differences=differences)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = audit(a.folder)
    save(a.output,result)
    print({k:v for k,v in result.items() if k not in ('checks','differences','comparison_inputs')})
    if result['difference_count']:
        raise SystemExit(2)
