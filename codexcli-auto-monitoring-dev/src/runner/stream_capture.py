from __future__ import annotations

import json
import pathlib
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import TextIO

from .sanitize import sanitize_value
from .spool import EventSpoolWriter


@dataclass(frozen=True)
class CaptureRequest:
    run_id: str
    workdir: str
    command: list[str]
    runtime_root: str
    capture_seconds: float = 3.0


@dataclass(frozen=True)
class CaptureResult:
    run_id: str
    command: list[str]
    returncode: int | None
    total_events: int
    stdout_events: int
    stderr_events: int
    spool_path: str


class _Counters:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.total = 0
        self.stdout_events = 0
        self.stderr_events = 0

    def mark(self, source: str) -> None:
        with self.lock:
            self.total += 1
            if source == "stdout":
                self.stdout_events += 1
            elif source == "stderr":
                self.stderr_events += 1


def _read_stream(source: str, stream: TextIO, spool: EventSpoolWriter, counters: _Counters) -> None:
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
            counters.mark("stdout")
        else:
            spool.emit(source="stderr", event_type="cli.stderr", payload={"line": sanitize_value(line[:4000])})
            counters.mark("stderr")


def capture_streams(req: CaptureRequest) -> CaptureResult:
    workdir = pathlib.Path(req.workdir).resolve()
    if not workdir.exists() or not workdir.is_dir():
        raise ValueError(f"invalid workdir: {workdir}")

    run_dir = pathlib.Path(req.runtime_root).resolve() / req.run_id
    spool_path = run_dir / "spool" / "events.ndjson"
    spool = EventSpoolWriter(run_id=req.run_id, spool_path=spool_path)
    counters = _Counters()

    proc = subprocess.Popen(
        req.command,
        cwd=str(workdir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    t_out = threading.Thread(target=_read_stream, args=("stdout", proc.stdout, spool, counters), daemon=True)
    t_err = threading.Thread(target=_read_stream, args=("stderr", proc.stderr, spool, counters), daemon=True)
    t_out.start()
    t_err.start()

    deadline = time.time() + max(req.capture_seconds, 0.1)
    while time.time() < deadline and proc.poll() is None:
        time.sleep(0.05)

    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

    t_out.join(timeout=2)
    t_err.join(timeout=2)
    spool.close()

    return CaptureResult(
        run_id=req.run_id,
        command=req.command,
        returncode=proc.returncode,
        total_events=counters.total,
        stdout_events=counters.stdout_events,
        stderr_events=counters.stderr_events,
        spool_path=str(spool_path),
    )
