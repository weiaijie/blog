"""Check every historical close against the original as-of monitor, then regroup runs."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from itertools import groupby
import json
import math
from pathlib import Path
import sys

import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.risk_monitor import analyze, load_config
from etf_research.long_history import load_long_history
from etf_research.publication import sha

FIELDS = dict(current_drawdown_warning='current_drawdown', observed_year_drawdown_limit='year_drawdown',
              volatility_limit='rolling_volatility', volatility_warning='rolling_volatility',
              var_limit='daily_var', sharpe_below_or_equal_target='rolling_sharpe',
              daily_move_warning='latest_daily_return')


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def require(ok, label):
    if not ok:
        raise ValueError('Risk audit mismatch: ' + str(label))


def check_one(job):
    run, nav_path, daily, risk, days, endpoint = job
    df = pd.read_csv(nav_path, dtype={'date':str})
    require(df.date.tolist() == days == [row['date'] for row in daily], run+' dates')
    idx = pd.DatetimeIndex(days)
    nav = df.equity.to_numpy()
    by_rule = {rule: [] for rule in FIELDS}
    for i, row in enumerate(daily, 1):
        result = analyze(idx[:i], nav[:i], risk)
        result['year_drawdown'] = result['years'][-1]['max_drawdown']
        for field in set(FIELDS.values()):
            ref, actual = result[field], row[field]
            require((actual == '' if ref is None else actual != '' and
                     math.isclose(float(actual), ref, abs_tol=1e-12, rel_tol=1e-12)), (run,row['date'],field))
        for rule, field in FIELDS.items():
            state = 'active' if rule in result['alerts'] else ('unknown' if result[field] is None else 'clear')
            require(row[rule] == state, (run,row['date'],rule))
            by_rule[rule].append(state)
    require(result['alerts'] == endpoint['alerts'] and result['as_of'] == endpoint['as_of'], run+' sealed endpoint')
    summaries, events = [], []
    for rule, flags in by_rule.items():
        found = []
        for flag, positions in groupby(range(len(days)), key=flags.__getitem__):
            if flag != 'active':
                continue
            group = list(positions)
            start, end = group[0], group[-1]
            after = flags[end+1] if end+1 < len(flags) else None
            cleared = days[end+1] if after == 'clear' else ''
            reason = 'year_reset' if cleared and rule == 'observed_year_drawdown_limit' and cleared[:4]!=days[end][:4] else 'threshold'
            found.append(dict(run=run, rule=rule, start=days[start], last_active=days[end], sessions=str(len(group)),
                              cleared=cleared, clearance_reason=reason if cleared else '',
                              status='cleared' if cleared else ('open' if after is None else 'interrupted_unknown')))
        events.extend(found)
        eligible = [d for d, f in zip(days,flags) if f != 'unknown']
        first = next(iter(found), {})
        summaries.append(dict(run=run, rule=rule, first_evaluable=next(iter(eligible), ''),
            eligible_sessions=str(len(eligible)), unknown_sessions=str(flags.count('unknown')),
            active_sessions=str(flags.count('active')), episode_count=str(len(found)),
            first_hit=first.get('start',''), first_sessions=first.get('sessions',''),
            first_cleared=first.get('cleared',''), first_status=first.get('status',''),
            longest_sessions=str(max((int(e['sessions']) for e in found), default=0)), end_state=flags[-1]))
    return summaries, events


def verify(folder, workers):
    cfg = load_config(ROOT/'config/research.json', ROOT)
    sources = json.loads((folder/'sources.json').read_text())
    results = ROOT/cfg['history_results']
    risk_path = ROOT/'reports/2026-11-06-close/risk.json'
    sealed = json.loads(risk_path.read_text())
    accounts = sorted(x['run'] for x in json.loads(results.read_text())['results'])
    data = load_long_history(ROOT/'data/snapshots')
    days = list(map(str, data.sessions))
    inputs = [ROOT/'config/research.json', results, *(results.parent/(r+'_daily.csv') for r in accounts)]
    require(sources == dict(scope='historical_only', start=days[0], end=days[-1], sessions=len(days),
        runs=len(accounts), settings=cfg['risk'], input_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in inputs},
        source_manifests=data.provenance['manifests_sha256'], reference_sha256=sha(risk_path)), 'provenance')
    grouped = {run:[] for run in accounts}
    for row in read_csv(folder/'daily.csv'):
        grouped[row['run']].append(row)
    endpoints = {r['run']: r for r in sealed['history']}
    jobs = [(r, results.parent/(r+'_daily.csv'), grouped[r], cfg['risk'], days, endpoints[r]) for r in accounts]
    summaries, events = [], []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for summary, episodes in pool.map(check_one, jobs):
            summaries.extend(summary)
            events.extend(episodes)
    opened = [e for e in events if e['status']=='open']
    for name, expected in [('summary',summaries),('episodes',events),('open_at_end',opened)]:
        require(read_csv(folder/(name+'.csv')) == expected, name)
    print(f'PASS {len(days)*len(accounts)} as-of closes, {len(days)*len(accounts)*len(FIELDS)} rule states, '
          f'{len(summaries)} summaries, {len(events)} episodes, {len(opened)} open')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', required=True, type=Path)
    p.add_argument('--workers', type=int, default=2)
    a = p.parse_args()
    verify(a.folder, a.workers)
