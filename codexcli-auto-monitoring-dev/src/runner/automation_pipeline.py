from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .spool import EventSpoolWriter

def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class AutomationRequest:
    run_id: str
    runtime_root: str
    scenario: str = "default"
    fail: bool = False


@dataclass(frozen=True)
class AutomationResult:
    run_id: str
    scenario: str
    step_status: str
    screenshot_path: str
    video_path: str
    trace_path: str
    manifest_path: str


def run_mock_automation(req: AutomationRequest) -> AutomationResult:
    run_dir = pathlib.Path(req.runtime_root).resolve() / req.run_id
    spool_path = run_dir / "spool" / "events.ndjson"
    spool = EventSpoolWriter(run_id=req.run_id, spool_path=spool_path)
    art_root = run_dir / "artifacts"
    ss_dir = art_root / "screenshots"
    vd_dir = art_root / "videos"
    tr_dir = art_root / "traces"
    for d in (ss_dir, vd_dir, tr_dir):
        d.mkdir(parents=True, exist_ok=True)

    step_id = f"mock-{req.scenario}"
    spool.emit(
        source="automation",
        event_type="step.started",
        payload={"step_id": step_id, "scenario": req.scenario},
    )

    screenshot_path = ss_dir / f"{step_id}.png"
    video_path = vd_dir / f"{step_id}.webm"
    trace_path = tr_dir / f"{step_id}.zip"

    # Minimal placeholder artifacts for end-to-end wiring.
    screenshot_path.write_bytes(b"\x89PNG\r\n\x1a\nmock-screenshot")
    video_path.write_bytes(b"mock-video")
    trace_path.write_bytes(b"mock-trace-zip")

    manifest_path = art_root / "manifest.ndjson"
    for p, artifact_type in (
        (screenshot_path, "screenshot"),
        (video_path, "video"),
        (trace_path, "trace"),
    ):
        item = {
            "schema_version": "1.0",
            "ts": _utc_iso(),
            "run_id": req.run_id,
            "step_id": step_id,
            "artifact_type": artifact_type,
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "sha256": _sha256(p),
        }
        with manifest_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        spool.emit(
            source="automation",
            event_type="artifact.created",
            payload=item,
        )

    step_status = "failed" if req.fail else "completed"
    spool.emit(
        source="automation",
        event_type=f"step.{step_status}",
        payload={"step_id": step_id, "scenario": req.scenario},
    )
    spool.close()

    return AutomationResult(
        run_id=req.run_id,
        scenario=req.scenario,
        step_status=step_status,
        screenshot_path=str(screenshot_path),
        video_path=str(video_path),
        trace_path=str(trace_path),
        manifest_path=str(manifest_path),
    )
