from __future__ import annotations

import json
import pathlib
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, TextIO

from .heartbeat_state import HeartbeatRequest, write_heartbeat
from .sanitize import sanitize_value
from .spool import EventSpoolWriter


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: datetime) -> str:
    return dt.isoformat()


@dataclass(frozen=True)
class LiveMonitorRequest:
    run_id: str
    workdir: str
    command: list[str]
    runtime_root: str
    duration_seconds: float = 10.0
    heartbeat_interval_seconds: float = 1.0
    t_dead_seconds: float = 20.0
    t_idle_seconds: float = 45.0
    t_stall_seconds: float = 300.0


@dataclass(frozen=True)
class LiveMonitorResult:
    run_id: str
    returncode: int | None
    total_events: int
    stdout_events: int
    stderr_events: int
    spool_path: str
    heartbeat_path: str
    final_state: str


class _SharedState:
    def __init__(self) -> None:
        now = _utc_now()
        self.lock = threading.Lock()
        self.last_stdout = now
        self.last_stderr = now
        self.last_event = now
        self.stdout_events = 0
        self.stderr_events = 0
        self.total_events = 0

    def mark_stdout(self) -> None:
        with self.lock:
            now = _utc_now()
            self.last_stdout = now
            self.last_event = now
            self.stdout_events += 1
            self.total_events += 1

    def mark_stderr(self) -> None:
        with self.lock:
            now = _utc_now()
            self.last_stderr = now
            self.last_event = now
            self.stderr_events += 1
            self.total_events += 1

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "last_stdout": self.last_stdout,
                "last_stderr": self.last_stderr,
                "last_event": self.last_event,
                "stdout_events": self.stdout_events,
                "stderr_events": self.stderr_events,
                "total_events": self.total_events,
            }


def _reader(source: str, stream: TextIO, spool: EventSpoolWriter, shared: _SharedState) -> None:
    for raw in iter(stream.readline, ""):
        line = raw.rstrip("\n")
        if not line:
            continue
        if source == "stdout":
            try:
                obj = json.loads(line)
                spool.emit(source="stdout", event_type="cli.jsonl", payload=sanitize_value(obj))
            except json.JSONDecodeError:
                spool.emit(source="stdout", event_type="cli.stdout.non_json", payload={"line": sanitize_value(line[:4000])})
            shared.mark_stdout()
        else:
            spool.emit(source="stderr", event_type="cli.stderr", payload={"line": sanitize_value(line[:4000])})
            shared.mark_stderr()


def run_live_monitor(req: LiveMonitorRequest) -> LiveMonitorResult:
    workdir = pathlib.Path(req.workdir).resolve()
    if not workdir.exists() or not workdir.is_dir():
        raise ValueError(f"invalid workdir: {workdir}")

    run_dir = pathlib.Path(req.runtime_root).resolve() / req.run_id
    spool = EventSpoolWriter(req.run_id, run_dir / "spool" / "events.ndjson")
    shared = _SharedState()

    proc = subprocess.Popen(
        req.command,
        cwd=str(workdir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    t_out = threading.Thread(target=_reader, args=("stdout", proc.stdout, spool, shared), daemon=True)
    t_err = threading.Thread(target=_reader, args=("stderr", proc.stderr, spool, shared), daemon=True)
    t_out.start()
    t_err.start()

    start = time.time()
    hb_path = ""
    final_state = "CLI_RUNNING"
    while time.time() - start < max(0.2, req.duration_seconds):
        snap = shared.snapshot()
        now = _utc_now()
        phase = "ai_running" if proc.poll() is None else "finalizing"
        hb = write_heartbeat(
            HeartbeatRequest(
                run_id=req.run_id,
                runtime_root=req.runtime_root,
                cli_alive=(proc.poll() is None),
                phase=phase,
                steps_done=int(snap["total_events"]),
                steps_total=max(1, int(snap["total_events"])),
                last_stdout_age_seconds=max(0.0, now.timestamp() - snap["last_stdout"].timestamp()),
                last_stderr_age_seconds=max(0.0, now.timestamp() - snap["last_stderr"].timestamp()),
                last_event_age_seconds=max(0.0, now.timestamp() - snap["last_event"].timestamp()),
                last_heartbeat_age_seconds=0.0,
                t_dead_seconds=req.t_dead_seconds,
                t_idle_seconds=req.t_idle_seconds,
                t_stall_seconds=req.t_stall_seconds,
            )
        )
        hb_path = hb.heartbeat_path
        final_state = hb.derived_state
        if proc.poll() is not None:
            break
        time.sleep(max(0.2, req.heartbeat_interval_seconds))

    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

    # Final heartbeat snapshot as finished phase.
    snap = shared.snapshot()
    now = _utc_now()
    hb_final = write_heartbeat(
        HeartbeatRequest(
            run_id=req.run_id,
            runtime_root=req.runtime_root,
            cli_alive=False,
            phase="finished",
            steps_done=int(snap["total_events"]),
            steps_total=max(1, int(snap["total_events"])),
            last_stdout_age_seconds=max(0.0, now.timestamp() - snap["last_stdout"].timestamp()),
            last_stderr_age_seconds=max(0.0, now.timestamp() - snap["last_stderr"].timestamp()),
            last_event_age_seconds=max(0.0, now.timestamp() - snap["last_event"].timestamp()),
            last_heartbeat_age_seconds=0.0,
            t_dead_seconds=req.t_dead_seconds,
            t_idle_seconds=req.t_idle_seconds,
            t_stall_seconds=req.t_stall_seconds,
        )
    )
    hb_path = hb_final.heartbeat_path
    final_state = hb_final.derived_state

    t_out.join(timeout=2)
    t_err.join(timeout=2)
    spool.close()

    snap = shared.snapshot()
    return LiveMonitorResult(
        run_id=req.run_id,
        returncode=proc.returncode,
        total_events=int(snap["total_events"]),
        stdout_events=int(snap["stdout_events"]),
        stderr_events=int(snap["stderr_events"]),
        spool_path=str((run_dir / "spool" / "events.ndjson").resolve()),
        heartbeat_path=hb_path,
        final_state=final_state,
    )
