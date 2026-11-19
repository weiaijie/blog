"""Independent offline check using raw SSE prices and a close-to-close P&L identity."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "reports/2026-11-05-long-history"


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def check(actual, expected, label):
    if actual != expected:
        raise ValueError(f"{label}: {actual} != {expected}")


def verify(output):
    report = json.loads((output / "summary.json").read_text())
    for name, digest in report["sources"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)
    for name, digest in report["market_sources"].items():
        path = ROOT / "data/snapshots" / name / "manifest.json"
        check(hashlib.sha256(path.read_bytes()).hexdigest(), digest, name)
    prices = {}
    symbols = ("510300", "511010")
    for symbol in symbols:
        path = ROOT / f"data/snapshots/2026-11-05-costs-11/official_full_{symbol}.body"
        raw = json.loads(path.read_bytes(), parse_float=D)
        for day, opening, high, low, close, *_ in raw["kline"]:
            key = str(day)
            prices[symbol, f"{key[:4]}-{key[4:6]}-{key[6:]}"] = (D(opening), D(high), D(low), D(close))

    original = json.loads((HISTORY / "audit.json").read_text())
    trades = defaultdict(list)
    income = Counter()
    costs = defaultdict(Counter)
    groups = defaultdict(list)
    for r in read_rows(output / "fills.csv"):
        groups[r["run"]].append(r)
    fill_count = 0
    outside_count = 0
    matrix = {r["run"]: r for r in report["matrix"]}
    check(set(matrix), set(original), "matrix coverage")
    for name, account in original.items():
        ledger = [t for t in account["journal"] if t["kind"] == "trade"]
        rows = groups.pop(name, [])
        check(len(rows), len(ledger), name)
        counts = Counter()
        excess_amount = D(0)
        for row, trade in zip(rows, ledger):
            day, symbol = trade["day"], trade["symbol"]
            op, hi, lo, close = prices[symbol, day]
            side, units, fill = trade["side"], trade["units"], D(trade["fill_price"])
            delta = units if side == "buy" else -units
            for k in ("day", "symbol", "side", "signal_date"):
                check(row[k], trade[k], k)
            check(int(row["units"]), units, "units")
            direction = "below" if fill < lo else "above" if fill > hi else "within"
            excess = abs(fill - min(max(fill, lo), hi))
            slip = (op - fill) * delta
            numeric = dict(raw_open=op, high=hi, low=lo, model_fill=fill, excess_per_unit=excess,
                           excess_amount=excess * units, excess_bps_of_open=excess / op * 10000,
                           signed_slippage=slip, commission=D(trade["commission"]), sell_tax=D(trade["tax"]))
            for k, value in numeric.items():
                check(D(row[k]), value, name + " " + k)
            check(row["direction"], direction, "range label")
            counts[direction] += 1
            excess_amount += excess * units
            trades[name, day, symbol].append((delta, op))
            costs[name, day].update(dict(slippage=slip, commission=-numeric["commission"], sell_tax=-numeric["sell_tax"]))
        for event in account["journal"]:
            if event["kind"] == "dividend_receivable":
                income[name, event["day"], event["symbol"]] += D(event["amount"])
        check(matrix[name]["above"], counts["above"], "above")
        check(matrix[name]["below"], counts["below"], "below")
        check(D(matrix[name]["excess_amount"]), excess_amount, "excess amount")
        fill_count += len(rows)
        outside_count += counts["above"] + counts["below"]
    check(len(groups), 0, "unrecognized fills")
    check(fill_count, report["trades"], "all fills")
    check(outside_count, report["outside"], "all outside")

    exported = defaultdict(list)
    for row in read_rows(output / "daily_pnl.csv"):
        exported[row["run"]].append(row)
    summaries = {p["run"]: p for p in report["portfolios"]}
    expected_names = {name for name in original if name.endswith("_100000_d1")}
    check(set(summaries), expected_names, "portfolio coverage")
    check(set(exported), expected_names, "daily coverage")
    count = 0
    for name, rows in exported.items():
        frozen = read_rows(HISTORY / (name + "_daily.csv"))
        check(len(rows), len(frozen), name + " calendar")
        prior_nav = D(100000)
        prior_units = dict.fromkeys(symbols, 0)
        prior_close = {}
        total = Counter()
        stress = Counter()
        dd = summaries[name]["max_drawdown"]
        for row, account in zip(rows, frozen):
            day = account["date"]
            check(row["date"], day, "date")
            components = {}
            for symbol in symbols:
                close = prices[symbol, day][-1]
                # Prior holdings earn close-to-close; today's signed trades earn open-to-close.
                price = prior_units[symbol] * (close - prior_close.get(symbol, close))
                price += sum(delta * (close - op) for delta, op in trades[name, day, symbol])
                components["price_" + symbol] = price
                components["dividend_" + symbol] = income[name, day, symbol]
                prior_close[symbol] = close
                prior_units[symbol] = int(account["units_" + symbol])
            for k in ("slippage", "commission", "sell_tax"):
                components[k] = costs[name, day][k]
            for k, v in components.items():
                check(D(row[k]), v, name + " " + day + " " + k)
            nav = D(account["equity"])
            check(D(row["close_equity"]), nav, "close NAV")
            check(sum(components.values()), nav - prior_nav, "daily NAV bridge")
            check(D(row["net_pnl"]), nav - prior_nav, "net P&L")
            total.update(components)
            if dd["peak"] < day <= dd["trough"]:
                stress.update(components)
            prior_nav = nav
            count += 1
        for k in total:
            check(total[k], D(summaries[name]["full_period"][k]), "period " + k)
            check(stress[k], D(dd["components"][k]), "drawdown " + k)
        check(sum(total.values()), D(summaries[name]["net_pnl"]), "period net")
    check(count, report["daily_reconciliations"], "all days")
    return dict(fills_checked=fill_count, daily_rows_checked=count, components_per_day=7,
                method="raw SSE OHLC, signed trades and prior-unit close-to-close revaluation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    print(json.dumps(verify(parser.parse_args().report)))
