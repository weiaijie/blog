#!/usr/bin/env python3
# Qoder mobile viewer + send helper (read history from local cache, send via UI automation)

import argparse
import json
import os
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import subprocess
import threading

DEFAULT_SOURCE = "~/Library/Application Support/Qoder/SharedClientCache/cli/projects"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8787
DEFAULT_QODER_ROOT = "~/Library/Application Support/Qoder"
DEFAULT_GLOBAL_DB = "~/Library/Application Support/Qoder/User/globalStorage/state.vscdb"
DEFAULT_LOCAL_DB = "~/Library/Application Support/Qoder/SharedClientCache/cache/db/local.db"

HTML_PATH = Path(__file__).with_name("qoder_mobile_ui.html")


def parse_ts(ts: str):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def flatten_content(parts, include_thinking=True, include_tool=True):
    texts = []
    for p in parts or []:
        if not isinstance(p, dict):
            texts.append(str(p))
            continue
        ptype = p.get("type")
        if ptype == "text":
            texts.append(p.get("text", ""))
        elif ptype == "thinking" and include_thinking:
            texts.append("[thinking] " + (p.get("thinking", "")))
        elif ptype == "tool_use" and include_tool:
            name = p.get("name")
            inp = p.get("input")
            texts.append(f"[tool_use] {name} {json.dumps(inp, ensure_ascii=False)}")
        elif ptype == "tool_result" and include_tool:
            texts.append(f"[tool_result] {p.get('content', '')}")
        else:
            if include_tool:
                texts.append(json.dumps(p, ensure_ascii=False))
    return "\n".join(t for t in texts if t is not None)


def try_decode_text(payload: str):
    if not payload:
        return None
    payload = payload.strip()
    if not payload:
        return None
    # try raw json
    if payload[0] in "[{":
        try:
            return json.loads(payload)
        except Exception:
            pass
    # try base64 -> utf-8 -> json
    try:
        import base64
        raw = base64.b64decode(payload + "===")
        try:
            text = raw.decode("utf-8")
        except Exception:
            text = None
        if text:
            t = text.strip()
            if t and t[0] in "[{":
                try:
                    return json.loads(t)
                except Exception:
                    return None
    except Exception:
        return None
    return None


def extract_text_from_summary(summary_text: str):
    if not summary_text:
        return None
    data = try_decode_text(summary_text)
    if not data:
        return None
    if isinstance(data, dict):
        # best-effort
        return json.dumps(data, ensure_ascii=False)
    if isinstance(data, list):
        texts = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if "content" in item and isinstance(item.get("content"), str) and item.get("content"):
                texts.append(item.get("content"))
            contents = item.get("contents") or item.get("content") or []
            if isinstance(contents, list):
                texts.append(flatten_content(contents, include_thinking=False, include_tool=False))
        merged = "\n".join(t for t in texts if t)
        return merged or None
    return None


def simplify_tool_payload(text: str):
    if not text:
        return text
    # try to parse json to show human-readable summary instead of raw payload
    try:
        data = json.loads(text)
    except Exception:
        return text
    if isinstance(data, dict):
        # common tool payload format
        name = data.get("name") or data.get("toolName") or data.get("tool_call") or data.get("tool")
        status = data.get("toolCallStatus") or data.get("status")
        results = data.get("results") or data.get("result")
        if isinstance(results, list) and results:
            first = results[0]
            content = first.get("content") if isinstance(first, dict) else None
            if isinstance(content, str) and content.strip():
                preview = content.strip().splitlines()[0][:160]
                return f"[tool] {name or 'tool'} · {status or 'ok'}\n{preview}"
        if isinstance(results, dict):
            content = results.get("content")
            if isinstance(content, str) and content.strip():
                preview = content.strip().splitlines()[0][:160]
                return f"[tool] {name or 'tool'} · {status or 'ok'}\n{preview}"
        # fallback: keep only key fields
        keep = {}
        for k in ("toolCallId", "toolCallStatus", "name", "toolName", "status"):
            if k in data:
                keep[k] = data[k]
        if keep:
            return "[tool] " + json.dumps(keep, ensure_ascii=False)
    return text


def scan_sources(sources, extra_files=None):
    jsonl_files = []
    for src in sources:
        src = Path(os.path.expanduser(src))
        if not src.exists():
            continue
        jsonl_files.extend(sorted(src.glob("*.jsonl")))
    if extra_files:
        jsonl_files.extend(extra_files)
    # de-dup
    uniq = []
    seen = set()
    for p in jsonl_files:
        ps = str(p)
        if ps not in seen:
            seen.add(ps)
            uniq.append(p)
    return uniq


def scan_qoder_sessions(qoder_root: Path):
    if not qoder_root.exists():
        return []
    files = []
    for p in qoder_root.rglob("*.session.execution.jsonl"):
        files.append(p)
    return files


def load_messages(sources, extra_files=None):
    messages = []
    jsonl_files = scan_sources(sources, extra_files=extra_files)
    for path in jsonl_files:
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue
                    msg = row.get("message")
                    if not isinstance(msg, dict):
                        continue
                    parts = msg.get("content") if isinstance(msg.get("content"), list) else None
                    content_full = flatten_content(parts) if parts is not None else (msg.get("content") or "")
                    content_display = (
                        flatten_content(parts, include_thinking=False, include_tool=False)
                        if parts is not None
                        else (msg.get("content") or "")
                    )
                    content = content_display if content_display else content_full
                    session_id = row.get("sessionId") or msg.get("sessionId") or "unknown"
                    source_key = str(path)
                    messages.append(
                        {
                            "session_id": session_id,
                            "session_key": f"{source_key}::{session_id}",
                            "timestamp": row.get("timestamp"),
                            "role": msg.get("role") or row.get("type") or "unknown",
                            "content": content,
                            "content_full": content_full,
                            "content_parts": parts,
                            "message_id": msg.get("id") or row.get("uuid"),
                            "parent_id": row.get("parentUuid"),
                            "source_file": source_key,
                        }
                    )
        except Exception:
            continue

    for m in messages:
        m["_dt"] = parse_ts(m.get("timestamp"))
    messages.sort(key=lambda x: x["_dt"] or datetime.min)
    return messages


def load_local_history(db_path: str):
    entries = []
    db_path = os.path.expanduser(db_path)
    if not os.path.exists(db_path):
        return entries
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT key, value FROM ItemTable WHERE key LIKE 'lingma.chat.localHistory.%'"
        )
        rows = cur.fetchall()
    except Exception:
        return entries
    for key, val in rows:
        if not val:
            continue
        try:
            data = json.loads(val)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            sid = item.get("sessionId") or item.get("id") or "unknown"
            title = (item.get("title") or "").strip()
            ts = item.get("timestamp")
            entries.append(
                {
                    "session_id": sid,
                    "title": title,
                    "timestamp": ts,
                    "source_key": f"{db_path}::{key}",
                }
            )
    return entries


def load_local_db_messages(db_path: str):
    db_path = os.path.expanduser(db_path)
    if not os.path.exists(db_path):
        return [], {}
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT session_id, session_title, project_id, project_name, gmt_create, gmt_modified "
            "FROM chat_session"
        )
        sessions = {}
        for row in cur.fetchall():
            sessions[row[0]] = {
                "session_id": row[0],
                "title": row[1] or f"Session {row[0]}",
                "project_id": row[2],
                "project_name": row[3],
                "gmt_create": row[4],
                "gmt_modified": row[5],
            }
        cur.execute(
            "SELECT id, session_id, role, content, summary, tool_result, model_info, gmt_create "
            "FROM chat_message ORDER BY gmt_create ASC"
        )
        messages = []
        for mid, sid, role, content, summary, tool_result, model_info, gmt_create in cur.fetchall():
            text = None
            if content:
                # content is encrypted, but try to decode if plaintext JSON
                parsed = try_decode_text(content)
                if parsed is not None:
                    if isinstance(parsed, (dict, list)):
                        text = json.dumps(parsed, ensure_ascii=False)
                    else:
                        text = str(parsed)
            if not text and summary:
                text = extract_text_from_summary(summary)
            if not text and tool_result:
                text = extract_text_from_summary(tool_result)
            if not text:
                # keep a placeholder for visibility
                text = "[encrypted]"
            # simplify tool payloads to avoid noisy json
            if (role or "").lower() == "tool":
                text = simplify_tool_payload(text)
            ts = None
            if gmt_create:
                try:
                    ts = datetime.fromtimestamp(int(gmt_create) / 1000).isoformat(sep=" ")
                except Exception:
                    ts = None
            dt = None
            if gmt_create:
                try:
                    dt = datetime.fromtimestamp(int(gmt_create) / 1000)
                except Exception:
                    dt = None
            messages.append(
                {
                    "session_id": sid,
                    "session_key": f"localdb::{sid}",
                    "timestamp": ts,
                    "role": role or "unknown",
                    "content": text,
                    "message_id": mid,
                    "source_file": db_path,
                    "_dt": dt,
                }
            )
        conn.close()
        return messages, sessions
    except Exception:
        return [], {}


def build_sessions(messages, local_history=None):
    sessions = {}
    for m in messages:
        sessions.setdefault(m["session_key"], []).append(m)

    items = []
    for skey, msgs in sessions.items():
        dts = [m.get("_dt") for m in msgs if m.get("_dt")]
        start = min(dts).isoformat(sep=" ") if dts else None
        end = max(dts).isoformat(sep=" ") if dts else None
        # title: first user text, preview: last assistant text
        title = None
        preview = None
        count = 0
        for m in msgs:
            role = (m.get("role") or "").lower()
            if role in ("user", "assistant"):
                count += 1
            if title is None and role == "user":
                t = (m.get("content") or "").strip()
                if t:
                    title = t.replace("\n", " ")[:80]
        for m in reversed(msgs):
            role = (m.get("role") or "").lower()
            if role == "assistant":
                t = (m.get("content") or "").strip()
                if t:
                    preview = t.replace("\n", " ")[:120]
                    break
        if not title:
            title = f"Session {msgs[0].get('session_id')}"[:80]
        items.append(
            {
                "session_key": skey,
                "session_id": msgs[0].get("session_id"),
                "title": title,
                "preview": preview or "",
                "start": start,
                "end": end,
                "count": count,
                "source_file": msgs[0].get("source_file"),
            }
        )
    # newest first
    items.sort(key=lambda x: x["end"] or "", reverse=True)

    # Add local history sessions that don't have messages on disk
    if local_history:
        existing_ids = {it["session_id"] for it in items}
        for lh in local_history:
            sid = lh.get("session_id") or "unknown"
            if sid in existing_ids:
                continue
            title = lh.get("title") or f"Session {sid}"
            ts = lh.get("timestamp")
            start = end = None
            if ts:
                try:
                    end = datetime.fromtimestamp(int(ts) / 1000).isoformat(sep=" ")
                    start = end
                except Exception:
                    pass
            items.append(
                {
                    "session_key": f"local::{sid}",
                    "session_id": sid,
                    "title": title[:80],
                    "start": start,
                    "end": end,
                    "count": 0,
                    "source_file": lh.get("source_key"),
                }
            )
        items.sort(key=lambda x: x["end"] or "", reverse=True)
    return sessions, items


def parse_hotkey(hotkey: str):
    if not hotkey:
        return [], ""
    hotkey = hotkey.lower().replace(" ", "")
    parts = hotkey.split("+")
    mods = []
    key = ""
    for p in parts:
        if p in ("cmd", "command"):
            mods.append("command down")
        elif p in ("shift",):
            mods.append("shift down")
        elif p in ("alt", "option"):
            mods.append("option down")
        elif p in ("ctrl", "control"):
            mods.append("control down")
        else:
            key = p
    return mods, key


def keypress_line(hotkey: str, delay: float = 0.1):
    mods, key = parse_hotkey(hotkey)
    if not key:
        return ""
    mods_expr = "{" + ", ".join(mods) + "}" if mods else "{}"
    return f"keystroke \"{applescript_escape(key)}\" using {mods_expr}\n            delay {delay}\n"


def applescript_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\"", "\\\"")


def parse_key_delay(token: str, default_delay: float):
    # token format: "cmd+l@0.3" or "cmd+l"
    if "@" not in token:
        return token, default_delay
    key, d = token.split("@", 1)
    try:
        return key.strip(), float(d)
    except Exception:
        return key.strip(), default_delay


def list_qoder_windows(app_name: str):
    # Try direct app scripting first (avoids System Events permission issues)
    script_direct = f'''
        tell application "{app_name}"
            try
                return (name of windows) as string
            on error
                return ""
            end try
        end tell
    '''
    raw = ""
    last_err = ""
    try:
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script_direct],
            check=False,
            capture_output=True,
            text=True,
        )
        raw = (result.stdout or "").strip()
        last_err = (result.stderr or "").strip()
    except Exception:
        raw = ""
        last_err = "direct osascript failed"
    if raw:
        # When cast to string, AppleScript joins with ", "
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if parts:
            return parts, last_err

    # Fallback to System Events (requires accessibility permission)
    # Try to activate the app first to ensure windows are accessible.
    script_se = f'''
        tell application "{app_name}" to activate
        delay 0.5
        tell application "System Events"
            if not (exists (process "{app_name}")) then
                return "COUNT=0||NAMES="
            end if
            tell process "{app_name}"
                try
                    set frontmost to true
                end try
                delay 0.2
                set out to ""
                repeat with w in windows
                    set out to out & (name of w) & "\\n"
                end repeat
                return "COUNT=" & (count of windows) & "||NAMES=" & out
            end tell
        end tell
    '''
    try:
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script_se],
            check=False,
            capture_output=True,
            text=True,
        )
        raw = (result.stdout or "").strip()
        last_err = (result.stderr or "").strip() or last_err
    except Exception:
        raw = ""
        last_err = last_err or "system events osascript failed"
    if not raw:
        return [], last_err or "empty output"
    if raw.startswith("COUNT="):
        try:
            parts = raw.split("||NAMES=", 1)
            count_part = parts[0].replace("COUNT=", "").strip()
            names_part = parts[1] if len(parts) > 1 else ""
            names = [line for line in names_part.splitlines() if line.strip()]
            if not names:
                try:
                    count = int(count_part)
                except Exception:
                    count = 0
                if count > 0:
                    names = [f"Window {i+1}" for i in range(count)]
            return names, last_err or f"count={count_part}"
        except Exception:
            return [], last_err or "parse failed"
    return [line for line in raw.splitlines() if line.strip()], last_err or "raw"


def send_to_qoder(
    text: str,
    app_name: str = "Qoder",
    focus_key: str = "",
    palette_cmd: str = "",
    pre_keys: str = "",
    target_window: str = "",
    clear_input: bool = False,
    key_delay: float = 0.1,
    pre_wait: float = 0.0,
    post_wait: float = 0.0,
):
    # copy to clipboard
    p = subprocess.Popen(["/usr/bin/pbcopy"], stdin=subprocess.PIPE)
    p.communicate(text.encode("utf-8"))

    focus_line = ""
    if focus_key:
        focus_line = keypress_line(focus_key, delay=0.1)

    palette_line = ""
    if palette_cmd:
        cmds = [c.strip() for c in palette_cmd.replace('|', ';;').split(';;') if c.strip()]
        lines = []
        for cmd in cmds:
            lines.append("keystroke \"p\" using {command down, shift down}\n")
            lines.append("            delay 0.1\n")
            lines.append(f"            keystroke \"{applescript_escape(cmd)}\"\n")
            lines.append("            delay 0.1\n")
            lines.append("            key code 36\n")
            lines.append("            delay 0.2\n")
        palette_line = "".join(lines)

    pre_line = ""
    if pre_keys:
        keys = [k.strip() for k in pre_keys.replace('|', ',').split(',') if k.strip()]
        lines = []
        for k in keys:
            kk, dd = parse_key_delay(k, key_delay)
            lines.append(keypress_line(kk, delay=dd))
        pre_line = "".join(lines)

    window_line = ""
    if target_window:
        matched = target_window
        try:
            windows, _ = list_qoder_windows(app_name)
            if windows:
                exact = [w for w in windows if w == target_window]
                if exact:
                    matched = exact[0]
                else:
                    contains = [w for w in windows if target_window in w]
                    if contains:
                        matched = contains[0]
        except Exception:
            matched = target_window
        try:
            with open("/tmp/qoder_last_window_match.txt", "w", encoding="utf-8") as f:
                f.write(matched or "")
        except Exception:
            pass
        win_index = None
        if matched and windows:
            try:
                win_index = windows.index(matched) + 1
            except Exception:
                win_index = None
        if matched:
            tw = applescript_escape(matched)
            idx_line = f"set index of win to {win_index}\n" if win_index else "set index of win to 1\n"
            window_line = (
                f"            try\n"
                f"                tell process \"{app_name}\"\n"
                f"                    set frontmost to true\n"
                f"                    try\n"
                f"                        click menu item \"{tw}\" of menu \"Window\" of menu bar 1\n"
                f"                    end try\n"
                f"                    delay 0.2\n"
                f"                    try\n"
                f"                        set win to first window whose name is \"{tw}\"\n"
                f"                        {idx_line}"
                f"                        try\n"
                f"                            perform action \"AXRaise\" of win\n"
                f"                        end try\n"
                f"                        try\n"
                f"                            set value of attribute \"AXMain\" of win to true\n"
                f"                        end try\n"
                f"                    end try\n"
                f"                end tell\n"
                f"            end try\n"
                f"            delay 0.3\n"
            )

    clear_line = ""
    if clear_input:
        clear_line = "keystroke \"a\" using {command down}\n            delay 0.05\n            key code 51\n            delay 0.05\n"

    script = f'''
        tell application "{app_name}" to activate
        delay 0.2
        tell application "System Events"
            if exists (process "{app_name}") then
                set frontmost of process "{app_name}" to true
            end if
        end tell
        delay 0.2
        tell application "System Events"
            {window_line}{palette_line}{pre_line}{focus_line}{clear_line}delay {pre_wait}
            keystroke "v" using {{command down}}
            delay {post_wait if post_wait > 0 else 0.1}
            -- key code 36
        end tell
    '''
    try:
        with open("/tmp/qoder_last.applescript", "w", encoding="utf-8") as f:
            f.write(script)
    except Exception:
        pass
    subprocess.run(["/usr/bin/osascript", "-e", script], check=False)


class Cache:
    def __init__(self, sources, auto_scan=False, qoder_root=None, global_db=None, local_db=None):
        self.sources = sources
        self.auto_scan = auto_scan
        self.qoder_root = qoder_root
        self.global_db = global_db
        self.local_db = local_db
        self.lock = threading.Lock()
        self._messages = []
        self._sessions = {}
        self._items = []
        self._last_mtime = 0.0
        self._last_scan = 0.0
        self._extra_files = []
        self._local_history = []
        self._local_history_map = {}
        self._local_db_messages = []
        self._local_db_sessions = {}

    def _current_mtime(self):
        mt = 0.0
        for p in scan_sources(self.sources, extra_files=self._extra_files):
            try:
                mt = max(mt, p.stat().st_mtime)
            except Exception:
                continue
        return mt

    def _maybe_scan(self):
        now = time.time()
        if self.auto_scan and self.qoder_root:
            if now - self._last_scan < 30:
                return
            self._extra_files = scan_qoder_sessions(self.qoder_root)
            self._last_scan = now
        if self.global_db:
            if not self._local_history or now - self._last_scan > 30:
                self._local_history = load_local_history(self.global_db)
                self._local_history_map = {}
                for it in self._local_history:
                    sid = it.get("session_id")
                    if not sid:
                        continue
                    self._local_history_map.setdefault(sid, []).append(it)
        if self.local_db:
            if not self._local_db_messages or now - self._last_scan > 30:
                self._local_db_messages, self._local_db_sessions = load_local_db_messages(self.local_db)

    def get(self, force=False):
        with self.lock:
            self._maybe_scan()
            mt = self._current_mtime()
            if force or mt > self._last_mtime or not self._messages:
                messages = load_messages(self.sources, extra_files=self._extra_files)
                if self._local_db_messages:
                    messages = messages + self._local_db_messages
                sessions, items = build_sessions(messages, local_history=self._local_history)
                self._messages = messages
                self._sessions = sessions
                self._items = items
                self._last_mtime = mt
            return self._messages, self._sessions, self._items

    def stats(self):
        with self.lock:
            self._maybe_scan()
            if not self._messages:
                messages = load_messages(self.sources, extra_files=self._extra_files)
                if self._local_db_messages:
                    messages = messages + self._local_db_messages
                sessions, items = build_sessions(messages, local_history=self._local_history)
                self._messages = messages
                self._sessions = sessions
                self._items = items
            return {
                "sources": self.sources,
                "auto_scan": self.auto_scan,
                "extra_files": len(self._extra_files),
                "local_history": len(self._local_history),
                "local_db_messages": len(self._local_db_messages),
                "local_db_sessions": len(self._local_db_sessions),
                "last_mtime": self._last_mtime,
                "last_scan": self._last_scan,
                "messages": len(self._messages),
                "sessions": len(self._items),
            }

    def local_messages(self, session_id: str):
        items = self._local_history_map.get(session_id, [])
        messages = []
        for it in items:
            ts = it.get("timestamp")
            iso = None
            if ts:
                try:
                    iso = datetime.fromtimestamp(int(ts) / 1000).isoformat(sep=" ")
                except Exception:
                    iso = None
            title = (it.get("title") or "").strip()
            if not title:
                continue
            messages.append(
                {
                    "session_id": session_id,
                    "session_key": f"local::{session_id}",
                    "timestamp": iso,
                    "role": "summary",
                    "content": title,
                }
            )
        try:
            messages.sort(key=lambda m: m.get("timestamp") or "")
        except Exception:
            pass
        return messages


def matches_query(text, q):
    if not q:
        return True
    if not text:
        return False
    return q.lower() in text.lower()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                if HTML_PATH.exists():
                    html = HTML_PATH.read_text(encoding="utf-8")
                else:
                    html = "<h1>Missing UI</h1>"
                return self._send(200, html, "text/html; charset=utf-8")

            if parsed.path == "/api/health":
                return self._send(200, {"ok": True, "time": time.time()})

            if parsed.path == "/api/stats":
                return self._send(200, self.server.cache.stats())

            if parsed.path == "/api/sessions":
                qs = parse_qs(parsed.query)
                q = (qs.get("q", [""])[0]).strip()
                refresh = qs.get("refresh", ["0"])[0] == "1"
                _, sessions, items = self.server.cache.get(force=refresh)
                if q:
                    filtered = []
                    for it in items:
                        msgs = sessions.get(it["session_key"], [])
                        hit = matches_query(it["title"], q)
                        if not hit:
                            for m in msgs:
                                if matches_query(m.get("content"), q):
                                    hit = True
                                    break
                        if hit:
                            filtered.append(it)
                    items = filtered
                return self._send(200, {"sessions": items})

            if parsed.path == "/api/session":
                qs = parse_qs(parsed.query)
                skey = qs.get("session_key", [""])[0]
                q = (qs.get("q", [""])[0]).strip()
                refresh = qs.get("refresh", ["0"])[0] == "1"
                _, sessions, _ = self.server.cache.get(force=refresh)
                msgs = sessions.get(skey, [])
                if not msgs and skey.startswith("local::"):
                    sid = skey.split("local::", 1)[1]
                    msgs = self.server.cache.local_messages(sid)
                if q:
                    msgs = [m for m in msgs if matches_query(m.get("content"), q)]
                for m in msgs:
                    m.pop("_dt", None)
                return self._send(200, {"session_key": skey, "messages": msgs})

            if parsed.path == "/api/sources":
                return self._send(200, {"sources": self.server.cache.sources})

            if parsed.path == "/api/windows":
                try:
                    windows, err = list_qoder_windows(self.server.app_name)
                except Exception as e:
                    return self._send(500, {"error": str(e), "windows": []})
                return self._send(200, {"windows": windows, "error": err or ""})

            return self._send(404, {"error": "not found"})
        except Exception as e:
            try:
                return self._send(500, {"error": str(e)})
            except Exception:
                return

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/api/send":
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length).decode("utf-8", errors="ignore")
                try:
                    data = json.loads(raw)
                except Exception:
                    data = {}
                text = (data.get("text") or "").strip()
                focus_key = (data.get("focus_key") or "").strip()
                palette_cmd = (data.get("palette_cmd") or "").strip()
                pre_keys = (data.get("pre_keys") or "").strip()
                target_window = (data.get("target_window") or "").strip()
                clear_input = bool(data.get("clear_input"))
                key_delay = float(data.get("key_delay", 0.1) or 0.1)
                pre_wait = float(data.get("pre_wait", 0.0) or 0.0)
                post_wait = float(data.get("post_wait", 0.1) or 0.1)
                if not text:
                    return self._send(400, {"error": "empty"})
                try:
                    send_to_qoder(
                        text,
                        app_name=self.server.app_name,
                        focus_key=focus_key,
                        palette_cmd=palette_cmd,
                        pre_keys=pre_keys,
                        target_window=target_window,
                        clear_input=clear_input,
                        key_delay=key_delay,
                        pre_wait=pre_wait,
                        post_wait=post_wait,
                    )
                except Exception as e:
                    return self._send(500, {"error": str(e)})
                return self._send(200, {"ok": True})
            return self._send(404, {"error": "not found"})
        except Exception as e:
            try:
                return self._send(500, {"error": str(e)})
            except Exception:
                return


def main():
    parser = argparse.ArgumentParser(description="Qoder mobile viewer + sender")
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help="Source dir(s) containing *.jsonl. Use comma-separated for multiple.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--app", default="Qoder", help="App name to activate")
    parser.add_argument("--global-db", default=DEFAULT_GLOBAL_DB, help="Global state.vscdb for local history")
    parser.add_argument("--local-db", default=DEFAULT_LOCAL_DB, help="Local Qoder db for chat history")
    parser.add_argument("--auto-scan", action="store_true", help="Auto scan Qoder for *.session.execution.jsonl")
    parser.add_argument("--qoder-root", default=DEFAULT_QODER_ROOT, help="Qoder root dir for auto scan")
    args = parser.parse_args()

    sources = [s.strip() for s in args.source.split(",") if s.strip()]
    if not sources:
        raise SystemExit("No source directory provided")

    for s in sources:
        p = Path(os.path.expanduser(s))
        if not p.exists():
            raise SystemExit(f"Source dir not found: {p}")

    qoder_root = Path(os.path.expanduser(args.qoder_root)) if args.auto_scan else None
    if args.auto_scan and not qoder_root.exists():
        raise SystemExit(f"Qoder root not found: {qoder_root}")

    server = HTTPServer((args.host, args.port), Handler)
    server.cache = Cache(
        sources,
        auto_scan=args.auto_scan,
        qoder_root=qoder_root,
        global_db=args.global_db,
        local_db=args.local_db,
    )
    server.app_name = args.app
    print(f"Server running on http://{args.host}:{args.port}")
    print(f"Sources: {sources}")
    if args.auto_scan:
        print(f"Auto scan: {qoder_root}")
    server.serve_forever()


if __name__ == "__main__":
    main()
