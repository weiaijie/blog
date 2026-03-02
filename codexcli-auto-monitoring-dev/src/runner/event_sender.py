from __future__ import annotations

import json
import pathlib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .api_client import RunApiClient


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chunked(items: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


@dataclass(frozen=True)
class SendRequest:
    run_id: str
    spool_path: str
    api_base: str
    runtime_root: str
    batch_size: int = 50
    max_retries: int = 3
    retry_base_seconds: float = 0.5


@dataclass(frozen=True)
class SendResult:
    run_id: str
    spool_path: str
    total_read: int
    total_sent: int
    failed_batches: int
    parse_errors: int
    dlq_path: str | None


def _read_events(spool_path: pathlib.Path) -> tuple[list[dict[str, Any]], int]:
    events: list[dict[str, Any]] = []
    parse_errors = 0

    if not spool_path.exists():
        raise ValueError(f"spool file does not exist: {spool_path}")

    for raw in spool_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                events.append(obj)
            else:
                parse_errors += 1
        except json.JSONDecodeError:
            parse_errors += 1
    return events, parse_errors


def _write_failed_batches(
    runtime_root: pathlib.Path,
    run_id: str,
    failed: list[dict[str, Any]],
) -> pathlib.Path | None:
    if not failed:
        return None

    dlq_dir = runtime_root / run_id / "dlq"
    dlq_dir.mkdir(parents=True, exist_ok=True)
    dlq_path = dlq_dir / "events.batch.failed.ndjson"
    with dlq_path.open("a", encoding="utf-8") as fh:
        for item in failed:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    return dlq_path


def send_spool_events(req: SendRequest) -> SendResult:
    spool_path = pathlib.Path(req.spool_path).resolve()
    runtime_root = pathlib.Path(req.runtime_root).resolve()

    events, parse_errors = _read_events(spool_path)
    if not events:
        return SendResult(
            run_id=req.run_id,
            spool_path=str(spool_path),
            total_read=0,
            total_sent=0,
            failed_batches=0,
            parse_errors=parse_errors,
            dlq_path=None,
        )

    client = RunApiClient(req.api_base)
    batches = _chunked(events, max(1, req.batch_size))
    sent = 0
    failed_payloads: list[dict[str, Any]] = []

    for i, batch in enumerate(batches, start=1):
        last_error: str | None = None
        ok = False
        for attempt in range(0, max(0, req.max_retries) + 1):
            try:
                client.post_events_batch(run_id=req.run_id, events=batch)
                sent += len(batch)
                ok = True
                break
            except RuntimeError as exc:
                last_error = str(exc)
                if attempt < req.max_retries:
                    backoff = req.retry_base_seconds * (2**attempt)
                    time.sleep(max(0.0, backoff))
        if not ok:
            failed_payloads.append(
                {
                    "schema_version": "1.0",
                    "run_id": req.run_id,
                    "batch_index": i,
                    "batch_size": len(batch),
                    "failed_at": _utc_iso(),
                    "error": last_error or "unknown send error",
                    "events": batch,
                }
            )

    dlq_path = _write_failed_batches(
        runtime_root=runtime_root,
        run_id=req.run_id,
        failed=failed_payloads,
    )

    return SendResult(
        run_id=req.run_id,
        spool_path=str(spool_path),
        total_read=len(events),
        total_sent=sent,
        failed_batches=len(failed_payloads),
        parse_errors=parse_errors,
        dlq_path=str(dlq_path) if dlq_path else None,
    )

