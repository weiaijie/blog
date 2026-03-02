from __future__ import annotations

import json
import os
import pathlib
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from .sanitize import sanitize_value
from .spool import EventSpoolWriter

def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class LaunchRequest:
    run_id: str
    prompt: str
    workdir: str
    full_auto: bool = True
    json_mode: bool = True
    skip_git_repo_check: bool = False
    sandbox: str | None = None
    output_last_message: str | None = None
    output_schema: str | None = None
    startup_wait_seconds: float = 1.0
    terminate_after_check: bool = True
    mock_command: str | None = None
    env_overrides: dict[str, str] | None = None


@dataclass(frozen=True)
class LaunchResult:
    run_id: str
    command: list[str]
    pid: int
    started_at: str
    initial_status: str
    initial_returncode: int | None
    final_returncode: int | None
    process_meta_path: str


def build_codex_command(req: LaunchRequest) -> list[str]:
    if req.mock_command:
        return ["bash", "-lc", req.mock_command]

    cmd: list[str] = ["codex", "exec"]
    if req.json_mode:
        cmd.append("--json")
    if req.full_auto:
        cmd.append("--full-auto")
    if req.skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    if req.sandbox:
        cmd.extend(["--sandbox", req.sandbox])
    if req.output_last_message:
        cmd.extend(["--output-last-message", req.output_last_message])
    if req.output_schema:
        cmd.extend(["--output-schema", req.output_schema])
    cmd.append(req.prompt)
    return cmd


def launch_codex_exec(req: LaunchRequest, runtime_root: str) -> LaunchResult:
    workdir = pathlib.Path(req.workdir).resolve()
    if not workdir.exists():
        raise ValueError(f"workdir does not exist: {workdir}")
    if not workdir.is_dir():
        raise ValueError(f"workdir is not a directory: {workdir}")

    command = build_codex_command(req)
    started_at = _utc_iso()
    run_dir = pathlib.Path(runtime_root).resolve() / req.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    spool = EventSpoolWriter(run_id=req.run_id, spool_path=run_dir / "spool" / "events.ndjson")
    spool.emit(
        source="runner",
        event_type="step.started",
        payload={
            "step": "codex_exec",
            "command": sanitize_value(command),
            "workdir": str(workdir),
        },
    )

    proc = subprocess.Popen(
        command,
        cwd=str(workdir),
        env={**os.environ, **(req.env_overrides or {})},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    time.sleep(max(req.startup_wait_seconds, 0.0))
    rc_initial = proc.poll()
    initial_status = "alive" if rc_initial is None else "exited"
    rc_final = rc_initial

    if req.terminate_after_check and rc_initial is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        rc_final = proc.returncode

    spool.emit(
        source="runner",
        event_type="cli.exited",
        payload={
            "pid": proc.pid,
            "initial_status": initial_status,
            "initial_returncode": rc_initial,
            "final_returncode": rc_final,
            "terminate_after_check": req.terminate_after_check,
        },
    )
    spool.close()

    meta_path = run_dir / "process.meta.json"
    meta = {
        "schema_version": "1.0",
        "run_id": req.run_id,
        "started_at": started_at,
        "pid": proc.pid,
        "command": command,
        "initial_status": initial_status,
        "initial_returncode": rc_initial,
        "final_returncode": rc_final,
        "terminate_after_check": req.terminate_after_check,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return LaunchResult(
        run_id=req.run_id,
        command=command,
        pid=proc.pid,
        started_at=started_at,
        initial_status=initial_status,
        initial_returncode=rc_initial,
        final_returncode=rc_final,
        process_meta_path=str(meta_path),
    )
