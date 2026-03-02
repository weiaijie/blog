from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .event_sender import SendRequest, send_spool_events
from .heartbeat_state import HeartbeatRequest, write_heartbeat
from .spool import EventSpoolWriter


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        return {}
    return {}


def _iter_spool_events(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
        except json.JSONDecodeError:
            continue
    return out


@dataclass(frozen=True)
class FinalizeRequest:
    run_id: str
    runtime_root: str
    canceled: bool = False
    canceled_reason: str | None = None


@dataclass(frozen=True)
class FinalizeResult:
    run_id: str
    final_status: str
    final_event_type: str
    final_path: str
    heartbeat_state_path: str


def finalize_run(req: FinalizeRequest) -> FinalizeResult:
    run_dir = pathlib.Path(req.runtime_root).resolve() / req.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    process_meta = _read_json(run_dir / "process.meta.json")
    spool_path = run_dir / "spool" / "events.ndjson"
    upload_report = run_dir / "upload" / "report.ndjson"

    process_rc = process_meta.get("final_returncode")
    events = _iter_spool_events(spool_path)
    has_step_failed = any(e.get("event_type") == "step.failed" for e in events)
    upload_failed = 0
    if upload_report.exists():
        for raw in upload_report.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if item.get("status") == "failed":
                    upload_failed += 1
            except json.JSONDecodeError:
                continue

    if req.canceled:
        final_status = "aborted"
        final_event_type = "run.aborted"
    elif has_step_failed or upload_failed > 0 or (process_rc not in (None, 0)):
        final_status = "failed"
        final_event_type = "run.failed"
    else:
        final_status = "completed"
        final_event_type = "run.completed"

    final_dir = run_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    final_path = final_dir / "run.final.json"

    summary = {
        "schema_version": "1.0",
        "run_id": req.run_id,
        "finalized_at": _utc_iso(),
        "final_status": final_status,
        "process_returncode": process_rc,
        "has_step_failed": has_step_failed,
        "upload_failed": upload_failed,
        "canceled": req.canceled,
        "canceled_reason": req.canceled_reason,
    }
    final_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    spool = EventSpoolWriter(req.run_id, spool_path)
    spool.emit(
        source="runner",
        event_type=final_event_type,
        payload=summary,
    )
    spool.close()

    hb = write_heartbeat(
        HeartbeatRequest(
            run_id=req.run_id,
            runtime_root=req.runtime_root,
            cli_alive=False,
            phase="finished",
            steps_done=0,
            steps_total=0,
            last_stdout_age_seconds=0.0,
            last_stderr_age_seconds=0.0,
            last_event_age_seconds=0.0,
            last_heartbeat_age_seconds=0.0,
        )
    )

    return FinalizeResult(
        run_id=req.run_id,
        final_status=final_status,
        final_event_type=final_event_type,
        final_path=str(final_path),
        heartbeat_state_path=hb.state_path,
    )


@dataclass(frozen=True)
class ReplayRequest:
    runtime_root: str
    api_base: str
    run_id: str | None = None
    archive_sent: bool = True
    batch_size: int = 50
    max_retries: int = 3


@dataclass(frozen=True)
class ReplayResult:
    scanned_runs: int
    sent_runs: int
    failed_runs: int
    report_path: str


def replay_spool_events(req: ReplayRequest) -> ReplayResult:
    runtime_root = pathlib.Path(req.runtime_root).resolve()
    if not runtime_root.exists():
        raise ValueError(f"runtime root not found: {runtime_root}")

    run_dirs: list[pathlib.Path]
    if req.run_id:
        run_dirs = [runtime_root / req.run_id]
    else:
        run_dirs = [p for p in runtime_root.iterdir() if p.is_dir()]

    scanned = 0
    sent_runs = 0
    failed_runs = 0
    report_dir = runtime_root / "replay"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.ndjson"

    with report_path.open("a", encoding="utf-8") as report:
        for run_dir in sorted(run_dirs):
            spool_path = run_dir / "spool" / "events.ndjson"
            if not spool_path.exists():
                continue
            scanned += 1
            run_id = run_dir.name
            result = send_spool_events(
                SendRequest(
                    run_id=run_id,
                    spool_path=str(spool_path),
                    api_base=req.api_base,
                    runtime_root=str(runtime_root),
                    batch_size=req.batch_size,
                    max_retries=req.max_retries,
                )
            )
            ok = result.failed_batches == 0
            if ok:
                sent_runs += 1
                if req.archive_sent:
                    archive = run_dir / "spool" / f"events.sent.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.ndjson"
                    spool_path.rename(archive)
            else:
                failed_runs += 1

            item = {
                "ts": _utc_iso(),
                "run_id": run_id,
                "total_read": result.total_read,
                "total_sent": result.total_sent,
                "failed_batches": result.failed_batches,
                "parse_errors": result.parse_errors,
                "dlq_path": result.dlq_path,
                "ok": ok,
            }
            report.write(json.dumps(item, ensure_ascii=False) + "\n")

    return ReplayResult(
        scanned_runs=scanned,
        sent_runs=sent_runs,
        failed_runs=failed_runs,
        report_path=str(report_path),
    )

