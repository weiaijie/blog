"""Build the historical risk episode ledger in a new directory."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.long_history import load_long_history
from etf_research.risk_monitor import load_config
from etf_research.rolling_alerts import RULES, episodes, metrics, states

REPORT = 'reports/2026-11-06-close/risk.json'
MAIN = 'monthly_50_50_base_100000_d1'
EVENT_FIELDS = 'run rule start last_active sessions status cleared clearance_reason'.split()


def save_csv(path, rows, columns):
    with path.open('x', encoding='utf-8', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def build(out):
    config_path = ROOT/'config/research.json'
    cfg = load_config(config_path, ROOT)
    ref = json.loads((ROOT/REPORT).read_text())
    risk = cfg['risk']
    if ref['settings'] != risk:
        raise ValueError('Sealed settings differ')
    inputs = {}
    def checked(path):
        name = path.relative_to(ROOT).as_posix()
        inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if inputs[name] != ref['input_sha256'][name]:
            raise ValueError('Historical input differs: ' + name)
    results = ROOT/cfg['history_results']
    checked(config_path)
    checked(results)
    data = load_long_history(ROOT/'data/snapshots')
    days = [str(d) for d in data.sessions]
    runs = sorted(x['run'] for x in json.loads(results.read_text())['results'])
    if len(runs) != 18 or set(runs) != {x['run'] for x in ref['history']} or len(set(runs)) != 18:
        raise ValueError('Expected all 18 historical accounts')
    out.mkdir(parents=True, exist_ok=False)
    events, summary = [], []
    for i, run in enumerate(runs):
        path = results.parent/(run + '_daily.csv')
        checked(path)
        df = pd.read_csv(path, dtype={'date':str})
        if df.date.tolist() != days:
            raise ValueError('NAV differs from verified calendar: ' + run)
        daily = metrics(df.equity, days, risk)
        for code, (_, col, _, _) in RULES.items():
            flags = states(daily[col], code, risk)
            found = episodes(run, code, days, flags)
            first = found[0] if found else {}
            eligible = [d for d, f in zip(days, flags) if f != 'unknown']
            summary.append(dict(run=run, rule=code, first_evaluable=next(iter(eligible), ''),
                eligible_sessions=len(eligible), unknown_sessions=len(days)-len(eligible),
                active_sessions=int((flags=='active').sum()), episode_count=len(found),
                first_hit=first.get('start',''), first_sessions=first.get('sessions',''),
                first_cleared=first.get('cleared',''), first_status=first.get('status',''),
                longest_sessions=max((r['sessions'] for r in found), default=0),
                end_state=flags[-1]))
            daily[code] = flags
            events.extend(found)
        daily.insert(0, 'run', run)
        daily.to_csv(out/'daily.csv', mode='a' if i else 'x', header=not i,
                     index_label='date', lineterminator='\n')
    opened = [e for e in events if e['status']=='open']
    save_csv(out/'episodes.csv', events, EVENT_FIELDS)
    save_csv(out/'open_at_end.csv', opened, EVENT_FIELDS)
    save_csv(out/'summary.csv', summary, list(summary[0]))
    provenance = dict(scope='historical_only', start=days[0], end=days[-1], sessions=len(days),
                      runs=len(runs), settings=risk, input_sha256=inputs,
                      source_manifests=data.provenance['manifests_sha256'],
                      reference_sha256=hashlib.sha256((ROOT/REPORT).read_bytes()).hexdigest())
    (out/'sources.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    write_report(out, summary, events, opened, provenance)


def write_report(out, summary, events, opened, src):
    statuses = {'open':'期末未解除','cleared':'已解除','interrupted_unknown':'后续不可算'}
    lines = ['# 18 个历史账户的滚动风险预警', '',
        f"历史区间 {src['start']} 至 {src['end']}，共 {src['sessions']:,} 个交易日。"
        f"6 个策略 × 3 档费用 × 7 条规则得到 {len(summary)} 项核对、{len(events)} 段预警。"
        f"其中 {sum(e['status']=='cleared' for e in events)} 段已解除，{len(opened)} 段期末未解除，"
        f"{sum(e['status']=='interrupted_unknown' for e in events)} 段因数据不可算而中断。不同账户可能在同一日预警。",
        '', '## 主观察账户：月度 50/50，基准费用', '',
        '|指标|首次越线|首段连续交易日|首段解除日|总段数|最长连续交易日|',
        '|---|---|---:|---|---:|---:|']
    for s in summary:
        if s['run'] == MAIN:
            lines.append('|{}|{}|{}|{}|{}|{}|'.format(RULES[s['rule']][0],s['first_hit'] or '未触发',
                s['first_sessions'] or '—', s['first_cleared'] or statuses.get(s['first_status'],'—'),
                s['episode_count'],s['longest_sessions']))
    lines += ['', '## 期末未解除（逐账户、逐指标）', '',
              '|账户|指标|本段首次越线|连续至|已预警交易日|','|---|---|---|---|---:|']
    for e in opened:
        lines.append(f"|{e['run']}|{RULES[e['rule']][0]}|{e['start']}|{e['last_active']}|{e['sessions']}|")
    lines += ['', '## 如何核对', '',
        '- [逐账户、逐规则汇总](summary.csv)：首次可算日、首次越线及首段解除日、累计和最长预警日数、期末状态。'
        '首次可算即越线时，更早的起点未知。零息现金账户夏普始终不可算。',
        '- [全部区间](episodes.csv)：start 至 last_active 均计入连续交易日；cleared 是首次可算且不再触线的收盘日，不计入预警。'
        '不可算会截断连续计数，不能证明解除。[期末未解除清单](open_at_end.csv)不推算未来解除日。',
        '- [逐日收盘值和七条状态](daily.csv)（active 越线、clear 未越线、unknown 不可算）；'
        '[输入哈希和计算配置](sources.json)。所有日期逐一对齐已核验的交易日历。',
        '- 当前回撤 >15%；年度最大回撤 ≥20%（沿用 1e-12 容差），以上年最后收盘为锚；'
        '年度值为年内截至当日的最大回撤，同年不会随反弹解除。year_reset 指跨年重新计算后解除，不代表净值已恢复。',
        '- 最近 252 个收盘收益，样本标准差年化；波动率 ≥25% 与 >30% 分别核对，'
        '夏普 ≤1（假设无风险利率 0），95% 历史日 VaR ≥3%（线性分位），单日涨跌绝对值 >5%。'
        '首次滚动计算需要 253 个净值；样本不足或夏普分母为零时留空。',
        '- 本表仅回顾历史，不拼接前瞻观察，不改变交易。复现：从项目根目录运行 '
        '`python scripts/build_rolling_risk.py --output 新目录`，然后运行 '
        '`python scripts/check_rolling_risk.py --folder 新目录`。检查器按每个历史收盘截断输入，用原监控重新计算。']
    (out/'PROGRESS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    build(p.parse_args().output)
