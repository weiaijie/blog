from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: datetime) -> str:
    return dt.isoformat()


def _from_age_seconds(now: datetime, age_seconds: float) -> datetime:
    age = max(0.0, float(age_seconds))
    return now.fromtimestamp(now.timestamp() - age, tz=timezone.utc)


@dataclass(frozen=True)
class HeartbeatRequest:
    run_id: str
    runtime_root: str
    cli_alive: bool
    phase: str
    steps_done: int
    steps_total: int
    last_stdout_age_seconds: float
    last_stderr_age_seconds: float
    last_event_age_seconds: float
    last_heartbeat_age_seconds: float
    t_dead_seconds: float = 20.0
    t_idle_seconds: float = 45.0
    t_stall_seconds: float = 300.0


@dataclass(frozen=True)
class HeartbeatResult:
    run_id: str
    derived_state: str
    runner_online: bool
    cli_alive: bool
    phase: str
    steps_done: int
    steps_total: int
    heartbeat_path: str
    state_path: str


def _load_prev_state(state_path: pathlib.Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        return {}
    return {}


def _derive_state(
    *,
    runner_online: bool,
    phase: str,
    cli_alive: bool,
    idle_seconds: float,
    t_idle: float,
    stall_seconds: float,
    t_stall: float,
    steps_unchanged: bool,
) -> str:
    if not runner_online:
        return "RUNNER_OFFLINE"
    if phase == "finished":
        return "FINISHED"
    if stall_seconds > t_stall and steps_unchanged:
        return "STALL_SUSPECTED"
    if cli_alive and idle_seconds > t_idle:
        return "AI_IDLE"
    if cli_alive:
        return "CLI_RUNNING"
    return "CLI_STOPPED"


def write_heartbeat(req: HeartbeatRequest) -> HeartbeatResult:
    now = _utc_now()
    last_stdout = _from_age_seconds(now, req.last_stdout_age_seconds)
    last_stderr = _from_age_seconds(now, req.last_stderr_age_seconds)
    last_event = _from_age_seconds(now, req.last_event_age_seconds)
    last_heartbeat = _from_age_seconds(now, req.last_heartbeat_age_seconds)

    runner_online = (now.timestamp() - last_heartbeat.timestamp()) <= req.t_dead_seconds
    idle_seconds = now.timestamp() - max(last_stdout.timestamp(), last_stderr.timestamp())
    stall_seconds = now.timestamp() - last_event.timestamp()

    run_dir = pathlib.Path(req.runtime_root).resolve() / req.run_id
    hb_dir = run_dir / "heartbeat"
    hb_dir.mkdir(parents=True, exist_ok=True)
    heartbeat_path = hb_dir / "heartbeat.ndjson"
    state_path = hb_dir / "state.json"

    prev = _load_prev_state(state_path)
    prev_steps_done = int(prev.get("steps_done", -1))
    steps_unchanged = prev_steps_done == req.steps_done

    derived_state = _derive_state(
        runner_online=runner_online,
        phase=req.phase,
        cli_alive=req.cli_alive,
        idle_seconds=idle_seconds,
        t_idle=req.t_idle_seconds,
        stall_seconds=stall_seconds,
        t_stall=req.t_stall_seconds,
        steps_unchanged=steps_unchanged,
    )

    event = {
        "schema_version": "1.0",
        "ts": _utc_iso(now),
        "run_id": req.run_id,
        "event_type": "heartbeat",
        "payload": {
            "runner_online": runner_online,
            "cli_alive": req.cli_alive,
            "phase": req.phase,
            "steps_done": req.steps_done,
            "steps_total": req.steps_total,
            "last_stdout_ts": _utc_iso(last_stdout),
            "last_stderr_ts": _utc_iso(last_stderr),
            "last_event_ts": _utc_iso(last_event),
            "last_heartbeat_ts": _utc_iso(last_heartbeat),
            "thresholds": {
                "t_dead_seconds": req.t_dead_seconds,
                "t_idle_seconds": req.t_idle_seconds,
                "t_stall_seconds": req.t_stall_seconds,
            },
            "derived_state": derived_state,
        },
    }
    with heartbeat_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    new_state = {
        "updated_at": _utc_iso(now),
        "derived_state": derived_state,
        "runner_online": runner_online,
        "cli_alive": req.cli_alive,
        "phase": req.phase,
        "steps_done": req.steps_done,
        "steps_total": req.steps_total,
    }
    state_path.write_text(json.dumps(new_state, ensure_ascii=False, indent=2), encoding="utf-8")

    return HeartbeatResult(
        run_id=req.run_id,
        derived_state=derived_state,
        runner_online=runner_online,
        cli_alive=req.cli_alive,
        phase=req.phase,
        steps_done=req.steps_done,
        steps_total=req.steps_total,
        heartbeat_path=str(heartbeat_path),
        state_path=str(state_path),
    )

