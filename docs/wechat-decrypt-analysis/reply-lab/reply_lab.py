"""Offline reply sampling. Never sends messages or calls a model/network API."""
import argparse
import collections
from contextlib import closing
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parent.parent


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def redact(text, aliases=()):
    # Mechanical masking only; human review remains mandatory.
    for alias in sorted(set(aliases), key=len, reverse=True):
        if len(alias) >= 2:
            text = text.replace(alias, "[联系人]")
    for pattern, replacement in [
        (r"https?://\S+", "[链接]"),
        (r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[邮箱]"),
        (r"(?:wxid_[\w]+|\b\d+@chatroom\b)", "[账号]"),
        (r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)", "[IP]"),
        (r"(?<!\d)\d{7,}[\dXx]?(?!\d)", "[号码]"),
        (r"(?i)(?:token|password|secret|密码|密钥)\s*[:=：]\s*\S+", "[敏感字段]"),
    ]:
        text = re.sub(pattern, replacement, text)
    return text


def make_candidates(messages, self_id, aliases=()):
    messages = sorted(messages, key=lambda r: (int(r["create_time"]), int(r["local_id"])))
    turns, current = [], []
    for row in messages:
        valid = (row["message_kind"] == "text" and row["sender_username"]
                 and 0 < len(row["clean_text"].strip()) <= 300)
        if not valid:
            if current:
                turns.append(current)
                current = []
            turns.append([])  # Barrier: do not bridge images/unknown speakers.
            continue
        if current and (row["sender_username"] != current[-1]["sender_username"]
                        or int(row["create_time"]) - int(current[-1]["create_time"]) > 120):
            turns.append(current)
            current = []
        current.append(row)
    if current:
        turns.append(current)
    result = []
    for i, turn in enumerate(turns):
        if not turn or i == 0 or turn[0]["sender_username"] != self_id:
            continue
        previous = turns[i - 1]
        if not previous or previous[0]["sender_username"] == self_id:
            continue
        if int(turn[0]["create_time"]) - int(previous[-1]["create_time"]) > 1800:
            continue
        answer = [redact(r["clean_text"], aliases) for r in turn]
        if not 6 <= sum(map(len, answer)) <= 180 or len(answer) > 5 or len(previous) > 5:
            continue
        history = [previous]
        for earlier in reversed(turns[max(0, i - 4):i - 1]):
            if not earlier or int(history[0][0]["create_time"]) - int(earlier[-1]["create_time"]) > 1800:
                break
            history.insert(0, earlier)
        context_rows = [r for block in history for r in block]
        if sum(len(r["clean_text"]) for r in context_rows) > 1200:
            continue
        chat = turn[0]["chat_username"]
        context = [{"role": "我" if r["sender_username"] == self_id else "对方",
                    "text": redact(r["clean_text"], aliases)} for r in context_rows]
        result.append({
            "id": digest(chat + ':' + turn[0]["db_file"] + ':' + turn[0]["local_id"]),
            "chat_id": digest(chat), "date": turn[0]["create_datetime"][:10],
            "object_type": "群聊" if turn[0]["is_group"] == "True" else "待确认",
            "context": context, "reference": answer,
            "source": [{k: r[k] for k in ("db_file", "table_name", "local_id", "sender_username")} for r in context_rows + turn],
            "identity_verified": False, "privacy_reviewed": False,
            "approved": False, "intent": "", "facts": "",
        })
    return result


def verify_identity(sample, database_dir):
    # Verify CSV sender IDs against original decrypted SQLite, without importing MCP.
    for source in sample["source"]:
        filename = source["db_file"]
        if Path(filename).name != filename or not re.fullmatch(r"message_\d+\.db", filename):
            return False
        table = source["table_name"]
        if not re.fullmatch(r"Msg_[0-9a-fA-F]{32}", table):
            return False
        db = database_dir / filename
        with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
            found = conn.execute(
                f'SELECT n.user_name FROM "{table}" m JOIN Name2Id n ON n.rowid=m.real_sender_id WHERE m.local_id=?',
                (int(source["local_id"]),)).fetchall()
        if len(found) != 1 or found[0][0] != source["sender_username"]:
            return False
    return True


def prepare(out):
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError("输出目录非空，请使用新目录，避免覆盖人工评价")
    self_path = BASE / "analysis_output/self_messages_cleaned.csv"
    senders, chats, metadata = collections.Counter(), collections.Counter(), {}
    latest = 0
    for row in rows(self_path):
        senders[row["sender_username"]] += 1
        latest = max(latest, int(row["create_time"]))
    if len(senders) != 1 or not next(iter(senders)):
        raise ValueError("本人发送者不唯一，需先核对")
    self_id = next(iter(senders))
    config = read_json(ROOT / "wechat-decrypt/config.json")
    account = Path(config["db_dir"]).parent.name
    if self_id not in (account, re.sub(r"_[0-9a-fA-F]{4,}$", "", account)):
        raise ValueError("历史导出本人身份与当前配置不一致")
    cutoff = latest - 180 * 86400
    for row in rows(self_path):
        chat = row["chat_username"]
        if row["message_kind"] == "text" and int(row["create_time"]) >= cutoff and chat != self_id:
            chats[chat] += 1
            metadata[chat] = row
    # Limit collection to the most active recent eight private and four group chats.
    selected = []
    for group, count in (("False", 8), ("True", 4)):
        selected += [chat for chat, _ in chats.most_common() if metadata[chat]["is_group"] == group][:count]
    gathered = {chat: [] for chat in selected}
    for row in rows(BASE / "analysis_output/all_messages_cleaned.csv"):
        if row["chat_username"] in gathered and int(row["create_time"]) >= cutoff:
            gathered[row["chat_username"]].append(row)
    aliases = [metadata[c][key] for c in selected for key in ("chat_name", "remark", "nick_name", "alias", "chat_username")]
    candidates, seen, dates = [], set(), collections.Counter()
    for chat in selected:
        entries = make_candidates(gathered[chat], self_id, aliases)
        kept = 0
        for entry in reversed(entries):
            fingerprint = digest(json.dumps([entry["context"], entry["reference"]], ensure_ascii=False))
            day = (entry["chat_id"], entry["date"])
            if fingerprint in seen or dates[day] or kept >= 6:
                continue
            if not verify_identity(entry, ROOT / "wechat-decrypt/decrypted/message"):
                continue
            entry["identity_verified"] = True
            candidates.append(entry)
            dates[day] += 1
            seen.add(fingerprint)
            kept += 1
    write_json(out / "candidates.json", candidates)
    write_json(out / "contact-map.private.json", {digest(c): metadata[c]["chat_name"] for c in selected})
    summary = {"self_rows": sum(senders.values()), "self_identity_matches_config": True,
               "source_latest": dt.datetime.fromtimestamp(latest).isoformat(),
               "lookback_days": 180, "selected_chats": len(selected),
               "candidates": len(candidates), "identity_verified": len(candidates),
               "object_types": dict(collections.Counter(x["object_type"] for x in candidates)),
               "privacy": "机械遮罩，尚未人工复核，不可视为完全匿名", "model_calls": 0}
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


def split_samples(samples):
    approved = [s for s in samples if s.get("approved")]
    if len({s["id"] for s in approved}) != len(approved):
        raise ValueError("样本 ID 重复，不能进入评测")
    for s in approved:
        if not s.get("privacy_reviewed") or not s.get("identity_verified"):
            raise ValueError("批准样本必须完成身份和隐私复核")
        if s["object_type"] not in ("同事", "领导", "家人", "群聊"):
            raise ValueError("对象类型待确认")
        if not s.get("intent", "").strip():
            raise ValueError("回复草稿模式需要本人表达意图")
    # Whole contacts stay in one split, preventing adjacent conversation leakage.
    groups = collections.defaultdict(list)
    for s in approved:
        groups[s["chat_id"]].append(s)
    dev, evaluation = [], []
    for chat in sorted(groups, key=digest):
        (dev if len(dev) < 10 else evaluation).extend(groups[chat])
    if not dev or not evaluation:
        raise ValueError("需足够的已批准样本和独立聊天对象，才能划分开发/评测集")
    return dev, evaluation


def public_input(sample):
    return {k: sample[k] for k in ("id", "object_type", "context", "intent", "facts")}


def build(source, out):
    dev, evaluation = split_samples(read_json(source))
    if out.exists() and any(out.iterdir()):
        raise ValueError("输出目录非空")
    out.mkdir(parents=True, exist_ok=True)
    instruction = (HERE / "prompt.txt").read_text(encoding="utf-8")
    write_json(out / "manifest.json", {
        "mode": "intent_provided_reply_draft",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "prompt_sha256": hashlib.sha256(instruction.encode()).hexdigest(),
        "dev_ids": [s["id"] for s in dev], "eval_ids": [s["id"] for s in evaluation],
        "dev_types": dict(collections.Counter(s["object_type"] for s in dev)),
        "eval_types": dict(collections.Counter(s["object_type"] for s in evaluation)),
        "shared_chats": sorted({s["chat_id"] for s in dev} & {s["chat_id"] for s in evaluation}),
        "required_eval_per_type": 5,
    })
    write_json(out / "dev.json", [{**public_input(s), "reply": s["reference"]} for s in dev])
    write_json(out / "eval-inputs.json", [public_input(s) for s in evaluation])
    write_json(out / "eval-references.private.json", [{"id": s["id"], "reference": s["reference"]} for s in evaluation])
    write_json(out / "requests.json", [{"id": s["id"], "messages": [
        {"role": "system", "content": instruction},
        {"role": "user", "content": json.dumps(public_input(s), ensure_ascii=False)}]} for s in evaluation])
    write_json(out / "ratings.json", [{"id": s["id"], "model": "", "reply": [], "rating": "", "factual_error": None, "extra_promise": None} for s in evaluation])
    print(json.dumps({"dev": len(dev), "eval": len(evaluation), "shared_chats": 0}))


def review(source, output):
    if output.exists():
        raise ValueError("筛选页已存在，请使用新文件名")
    payload = json.dumps(read_json(source), ensure_ascii=False).replace("<", "\\u003c")
    template = (HERE / "review.html").read_text(encoding="utf-8")
    output.write_text(template.replace("/*SAMPLES*/[]", payload), encoding="utf-8")
    print("已生成本地筛选页；不会自动保存，请使用导出按钮")


def score(path):
    data = read_json(path)
    manifest = read_json(path.parent / "manifest.json")
    actual_ids = [x["id"] for x in data]
    if len(set(actual_ids)) != len(actual_ids) or set(actual_ids) != set(manifest["eval_ids"]):
        raise ValueError("评价 ID 必须与本批评测清单完全一致，不能删除困难样本或重复计分")
    allowed = ("可直接用", "小改可用", "不像我")
    complete = [x for x in data if x.get("rating") in allowed
                and isinstance(x.get("reply"), list) and x["reply"]
                and all(isinstance(line, str) and line.strip() for line in x["reply"])
                and isinstance(x.get("model"), str) and x["model"].strip()
                and type(x.get("factual_error")) is bool and type(x.get("extra_promise")) is bool]
    usable = sum(x["rating"] != "不像我" for x in complete)
    coverage = all(manifest["eval_types"].get(kind, 0) >= 5 for kind in ("同事", "领导", "家人", "群聊"))
    fully_rated = bool(data) and len(complete) == len(data)
    numeric_gate = (fully_rated and coverage and usable / len(data) >= .8
                    and not any(x["factual_error"] or x["extra_promise"] for x in complete))
    print(json.dumps({"total": len(data), "rated": len(complete), "usable": usable,
                      "usable_rate": usable / len(complete) if complete else None,
                      "factual_errors": sum(x["factual_error"] for x in complete),
                      "extra_promises": sum(x["extra_promise"] for x in complete),
                      "eval_types": manifest["eval_types"], "coverage_met": coverage,
                      "numeric_gate_met": numeric_gate,
                      "status": "待完成评价" if not fully_rated else "已统计本人评价；数值门槛不替代本人验收"}, ensure_ascii=False))


def audit(source):
    data = read_json(source)
    report = {"candidates": len(data), "approved": sum(s.get("approved") is True for s in data),
              "identity_verified": sum(s.get("identity_verified") is True for s in data),
              "privacy_reviewed": sum(s.get("privacy_reviewed") is True for s in data),
              "intent_filled": sum(bool(s.get("intent", "").strip()) for s in data),
              "object_types": dict(collections.Counter(s["object_type"] for s in data))}
    try:
        dev, evaluation = split_samples(data)
        report["split"] = {"dev": len(dev), "eval": len(evaluation),
                           "eval_types": dict(collections.Counter(s["object_type"] for s in evaluation))}
    except ValueError as error:
        report["split_pending"] = str(error)
    print(json.dumps(report, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--out", type=Path, required=True)
    b = sub.add_parser("build")
    b.add_argument("--source", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    s = sub.add_parser("score")
    s.add_argument("--ratings", type=Path, required=True)
    r = sub.add_parser("review")
    r.add_argument("--source", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("audit")
    a.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.out)
    elif args.command == "build":
        build(args.source, args.out)
    elif args.command == "review":
        review(args.source, args.out)
    elif args.command == "audit":
        audit(args.source)
    else:
        score(args.ratings)


if __name__ == "__main__":
    main()
