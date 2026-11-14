"""Explain frozen close-to-close NAV and audit cost-model fills against admitted OHLC."""
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal as D
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from etf_research.long_history import load_long_history

HISTORY = ROOT / "reports/2026-11-05-long-history"
SYMBOLS = ("510300", "511010")
MAIN = "monthly_50_50_base_100000_d1"
COMPONENTS = ("price_510300", "price_511010", "dividend_510300", "dividend_511010",
              "slippage", "commission", "sell_tax")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fill_details(trade, bar):
    raw = D(trade["raw_price"])
    fill = D(trade["fill_price"])
    units = trade["units"]
    side = trade["side"]
    require(side in ("buy", "sell") and units > 0, "Invalid trade")
    require(raw == bar.open and bar.low <= raw <= bar.high, "Opening mark mismatch")
    require(D(trade["notional"]) == fill * units, "Notional mismatch")
    require(trade["signal_date"] < trade["day"], "Signal timestamp mismatch")
    signed = units if side == "buy" else -units
    slip = signed * (raw - fill)
    require(slip <= 0, "Favourable fill under adverse slippage model")
    excess = max(fill - bar.high, bar.low - fill, D(0))
    return dict(day=trade["day"], symbol=trade["symbol"], side=side, units=units,
                signal_date=trade["signal_date"], raw_open=raw, low=bar.low, high=bar.high,
                model_fill=fill, direction="above" if fill > bar.high else "below" if fill < bar.low else "within",
                excess_per_unit=excess, excess_amount=excess * units,
                excess_bps_of_open=excess / raw * 10000, signed_slippage=slip,
                commission=D(trade["commission"]), sell_tax=D(trade["tax"]))


def reconcile_day(previous_units, closing_units, previous_close, bars, fills, entitlements):
    quantity_change = Counter()
    parts = dict.fromkeys(COMPONENTS, D(0))
    for fill in fills:
        symbol = fill["symbol"]
        qty = fill["units"] if fill["side"] == "buy" else -fill["units"]
        quantity_change[symbol] += qty
        parts["slippage"] += fill["signed_slippage"]
        parts["commission"] -= fill["commission"]
        parts["sell_tax"] -= fill["sell_tax"]
    for symbol in SYMBOLS:
        require(previous_units[symbol] + quantity_change[symbol] == closing_units[symbol],
                "Holdings do not match the trade ledger")
        bar = bars[symbol]
        parts["price_" + symbol] = (previous_units[symbol] * (bar.open - previous_close[symbol])
                                    + closing_units[symbol] * (bar.close - bar.open))
        parts["dividend_" + symbol] = entitlements[symbol]
    return parts


def aggregate(rows):
    return {key: sum((row[key] for row in rows), D(0)) for key in COMPONENTS}


def drawdown_span(nav):
    peak = 0
    start = end = 0
    worst = D(0)
    for i, value in enumerate(nav):
        if value > nav[peak]:
            peak = i
        depth = 1 - value / nav[peak]
        if depth > worst:
            worst, start, end = depth, peak, i
    return start, end, worst


def attribute(name, account, journal, fills, dataset):
    with (HISTORY / (name + "_daily.csv")).open(encoding="utf-8", newline="") as stream:
        daily = list(csv.DictReader(stream))
    days = [str(day) for day in dataset.sessions]
    require([row["date"] for row in daily] == days, "Incomplete NAV calendar")
    balances = {row["date"]: row for row in daily}
    dividends = defaultdict(Counter)
    payments = defaultdict(Counter)
    for event in dataset.dividends:
        shares = int(balances[str(event.record_date)]["units_" + event.symbol])
        amount = shares * event.per_share
        dividends[str(event.ex_date)][event.symbol] += amount
        payments[str(event.pay_date)][event.symbol] += amount
    actual_dividends = Counter()
    actual_payments = Counter()
    for entry in journal:
        kind = entry["kind"]
        if kind in ("dividend_receivable", "dividend_paid"):
            bucket = actual_dividends if kind == "dividend_receivable" else actual_payments
            bucket[entry["day"], entry["symbol"]] += D(entry["amount"])
    for expected, actual in ((dividends, actual_dividends), (payments, actual_payments)):
        flat = Counter({(day, symbol): amount for day, group in expected.items()
                        for symbol, amount in group.items()})
        require(actual == flat, "Official record-date units disagree with dividend ledger")

    by_day = defaultdict(list)
    for fill in fills:
        by_day[fill["day"]].append(fill)
    previous_units = dict.fromkeys(SYMBOLS, 0)
    previous_close = {s: dataset.bars[s][dataset.sessions[0]].open for s in SYMBOLS}
    cash = previous_nav = D(account["initial_cash"])
    receivable = D(0)
    rows = []
    nav = []
    for day, saved in zip(dataset.sessions, daily):
        key = str(day)
        bars = {s: dataset.bars[s][day] for s in SYMBOLS}
        closing = {s: int(saved["units_" + s]) for s in SYMBOLS}
        parts = reconcile_day(previous_units, closing, previous_close, bars, by_day[key], dividends[key])
        paid = sum(payments[key].values(), D(0))
        cash += paid
        receivable += sum(dividends[key].values(), D(0)) - paid
        for fill in by_day[key]:
            signed = fill["units"] if fill["side"] == "buy" else -fill["units"]
            cash -= signed * fill["model_fill"] + fill["commission"] + fill["sell_tax"]
        level = D(saved["equity"])
        require((cash, receivable) == (D(saved["cash"]), D(saved["receivables"])), name + " cash " + key)
        require(cash + receivable + sum(closing[s] * bars[s].close for s in SYMBOLS) == level,
                name + " marked balance " + key)
        net = sum(parts.values(), D(0))
        require(net == level - previous_nav, name + " P&L mismatch " + key)
        rows.append(dict(run=name, date=key, **parts, net_pnl=net, close_equity=level))
        nav.append(level)
        previous_units, previous_close, previous_nav = closing, {s: bars[s].close for s in SYMBOLS}, level

    start, end, depth = drawdown_span(nav)
    require(abs(depth + D(str(account["max_close_drawdown"]))) < D("1e-12"), "Drawdown mismatch")
    breakdown = aggregate(rows[start + 1:end + 1])
    require(sum(breakdown.values()) == nav[end] - nav[start], "Drawdown contribution mismatch")
    total = aggregate(rows)
    require(sum(total.values()) == D(account["ending_equity"]) - D(account["initial_cash"]), "Full P&L mismatch")
    return rows, dict(run=name, full_period=total, net_pnl=sum(total.values()),
                      max_drawdown=dict(peak=days[start], trough=days[end], peak_equity=nav[start],
                                        trough_equity=nav[end], fraction=depth, components=breakdown))


def markdown(report, fills):
    main = next(r for r in report["portfolios"] if r["run"] == MAIN)
    drawdown = main["max_drawdown"]
    full = main["full_period"]
    stress = drawdown["components"]
    lines = [
        "# 历史净收益来源与模型成交价核查",
        "",
        f"样本覆盖 {report['begin']} 至 {report['end']}，共 {report['sessions']:,} 个已核验交易日。",
        f"10 万元月度 50/50 基准费用组合期末净增 **{main['net_pnl']:,.2f} 元**。"
        f"下表把全期收益和 {drawdown['fraction']:.2%} 最大收盘回撤分别还原为金额。",
        "",
        "| 净值变动来源（元） | 全期 | 最大回撤期间 |",
        "|---|---:|---:|",
    ]
    labels = ("股票 ETF 价格变动", "债券 ETF 价格变动", "股票 ETF 分红权益", "债券 ETF 分红权益",
              "模型滑点", "佣金", "卖出税")
    for key, label in zip(COMPONENTS, labels):
        lines.append(f"| {label} | {full[key]:,.2f} | {stress[key]:,.2f} |")
    lines.extend([
        f"| **合计** | **{sum(full.values()):,.2f}** | **{sum(stress.values()):,.2f}** |",
        "",
        f"从 {drawdown['peak']} 收盘净值 {drawdown['peak_equity']:,.2f} 元，到 {drawdown['trough']} "
        f"收盘净值 {drawdown['trough_equity']:,.2f} 元。回撤归因从峰值收盘后的第一个交易日算起，包含谷值日。",
        "",
        "价格项采用未复权行情。昨日收盘持仓承担隔夜价格变动，当日交易后的持仓承担开盘至收盘价格变动。"
        "分红按登记日收盘份额计算，在除息日确认应收，支付日只把应收转成现金。读单只基金的贡献时应合看价格与分红两项，除息会反映在未复权价格中。",
        "",
        "全期金额按冻结的整手、费用和滑点模型计算，期末持仓按收盘价计值。分项为实际持仓路径上的金额，"
        "直接交易成本之和不包含假设改变费用后引起的份额、后续分红或再平衡差异。",
        "",
        "## 模型成交价与当日日线",
        "",
        f"全部 162 个固定场景共 {report['trades']:,} 笔模型成交，其中 **{report['outside']:,} 笔**"
        f"超出对应证券当日最高价或最低价，涉及 {report['affected_runs']} 个场景。每个场景均与原诊断计数核对。"
        "相同交易日和信号可能出现在多个场景，表中笔数不能用于估计实际成交概率。",
        "",
        "| ETF | 费用 | 模型成交数 | 高于最高价 | 低于最低价 | 最大超界幅度（相对开盘价，bp） |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for symbol in SYMBOLS:
        for cost in ("low", "base", "high"):
            group = [r for r in fills if r["symbol"] == symbol and r["run"].rsplit("_", 3)[1] == cost]
            above = sum(r["direction"] == "above" for r in group)
            below = sum(r["direction"] == "below" for r in group)
            maximum = max(r["excess_bps_of_open"] for r in group)
            lines.append(f"| {symbol} | {cost} | {len(group):,} | {above:,} | {below:,} | {maximum:.3f} |")
    main_range = next(r for r in report["matrix"] if r["run"] == MAIN)
    lines.extend([
        "",
        f"主组合共 {main_range['trades']} 笔，其中 {main_range['above']} 笔高于当日最高价、"
        f"{main_range['below']} 笔低于当日最低价。超界金额按超出最近日线边界的价差乘模型份额计算，"
        "该金额已包含在模型价格中，重复扣除会低估净值。日线内的价格也缺少订单簿深度、队列和实际成交回报。",
        "",
        "## 复核与复现",
        "",
        f"18 个主本金账户共 {report['daily_reconciliations']:,} 行逐日对账，金额使用 Decimal 精确比较。"
        "每天同时核对账面现金、应收分红、证券市值和净值变化。独立检查直接读取上交所日线，按旧持仓的收盘至收盘损益及当日成交的剩余日内损益重新计算。",
        "",
        "在项目目录执行以下命令，第二条命令在临时目录重建并逐字节比较已发布结果。",
        "",
        "```sh",
        "python scripts/check_historical_pnl.py --report reports/2026-11-07-historical-pnl",
        "python scripts/audit_historical_pnl.py --check reports/2026-11-07-historical-pnl",
        "```",
        "",
        "[逐笔成交明细](fills.csv) · [每日归因](daily_pnl.csv) · [全部组合、回撤区间及输入哈希](summary.json)",
        "",
        "费用、滑点、成交延迟和分红资格均沿用冻结协议。本轮结果属于历史研究，前瞻账户截至 2026-11-06，观察期为两个交易日。",
        "",
    ])
    return "\n".join(lines)


def build(output):
    dataset = load_long_history(ROOT / "data/snapshots")
    scenarios = read_json(HISTORY / "sensitivity.json")["results"]
    ledgers = read_json(HISTORY / "audit.json")
    diagnostics = {r["run"]: r for r in read_json(HISTORY / "execution_diagnostics.json")["runs"]}
    expected = {f"{s}_{c}_{capital}_d{delay}" for s in ("cash", "equity_hold", "bond_hold", "monthly_20_80", "monthly_50_50", "trend_120")
                for c in ("low", "base", "high") for capital in (10000, 100000, 1000000) for delay in (1, 2, 3)}
    require(len(scenarios) == 162 and {s["run"] for s in scenarios} == set(ledgers) == set(diagnostics) == expected,
            "Frozen matrix incomplete")
    all_fills, daily, portfolios, matrix = [], [], [], []
    for account in scenarios:
        name = account["run"]
        journal = ledgers[name]["journal"]
        fills = [dict(run=name, **fill_details(t, dataset.bars[t["symbol"]][date.fromisoformat(t["day"])]))
                 for t in journal if t["kind"] == "trade"]
        outside = [f for f in fills if f["direction"] != "within"]
        require(len(fills) == account["trades"] and len(outside) == diagnostics[name]["fills_outside_daily_range"],
                "Frozen fill counts disagree: " + name)
        for key, original, sign in (("signed_slippage", "slippage_cost", -1), ("commission", "commissions", 1),
                                    ("sell_tax", "sell_tax", 1)):
            require(sum(f[key] for f in fills) == sign * D(account[original]), "Cost mismatch: " + name)
        matrix.append(dict(run=name, trades=len(fills), above=sum(f["direction"] == "above" for f in fills),
                           below=sum(f["direction"] == "below" for f in fills), outside=len(outside),
                           max_excess_bps_of_open=max((f["excess_bps_of_open"] for f in fills), default=None),
                           excess_amount=sum((f["excess_amount"] for f in fills), D(0))))
        all_fills.extend(fills)
        if account["initial_cash"] == "100000" and account["execution_delay_sessions"] == 1:
            rows, summary = attribute(name, account, journal, fills, dataset)
            daily.extend(rows)
            portfolios.append(summary)
    require(len(portfolios) == 18, "Missing attribution accounts")
    sources = [HISTORY / f for f in ("audit.json", "execution_diagnostics.json", "sensitivity.json")]
    sources.extend(HISTORY / (p["run"] + "_daily.csv") for p in portfolios)
    report = dict(schema_version=1, begin=str(dataset.sessions[0]), end=str(dataset.sessions[-1]),
                  currency="CNY", precision="exact Decimal monetary identities", sessions=len(dataset.sessions),
                  daily_reconciliations=len(daily), trades=len(all_fills), outside=sum(r["outside"] for r in matrix),
                  affected_runs=sum(r["outside"] > 0 for r in matrix), portfolios=portfolios, matrix=matrix,
                  sources={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  market_sources=dataset.provenance["manifests_sha256"])
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "fills.csv", all_fills)
    write_csv(output / "daily_pnl.csv", daily)
    (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
                                       encoding="utf-8", newline="\n")
    (output / "PROGRESS.md").write_text(markdown(report, all_fills), encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="Publish to a new directory")
    mode.add_argument("--check", type=Path, help="Compare a fresh rebuild with existing artifacts")
    args = parser.parse_args()
    destination = args.output or args.check
    if args.output and destination.exists():
        parser.error("Output already exists. Use --check to verify or select a new directory.")
    if args.output:
        destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent if args.output else None) as temp:
        staged = Path(temp) / "result"
        report = build(staged)
        if args.check:
            for item in staged.iterdir():
                require(item.read_bytes() == (destination / item.name).read_bytes(), "Rebuild differs: " + item.name)
        else:
            staged.rename(destination)
    print({k: report[k] for k in ("trades", "outside", "affected_runs", "daily_reconciliations")})
