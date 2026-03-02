from __future__ import annotations

import json
import pathlib
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .api_client import RunApiClient


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class UploadRequest:
    run_id: str
    manifest_path: str
    api_base: str
    runtime_root: str
    skip_object_upload: bool = True


@dataclass(frozen=True)
class UploadResult:
    run_id: str
    manifest_path: str
    processed: int
    completed: int
    failed: int
    report_path: str


def _read_manifest(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"manifest not found: {path}")
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


def _upload_binary(upload_url: str, file_path: pathlib.Path) -> None:
    data = file_path.read_bytes()
    req = urllib.request.Request(url=upload_url, data=data, method="PUT")
    with urllib.request.urlopen(req, timeout=30):
        return


def upload_artifacts(req: UploadRequest) -> UploadResult:
    manifest_path = pathlib.Path(req.manifest_path).resolve()
    rows = _read_manifest(manifest_path)
    client = RunApiClient(req.api_base)

    run_dir = pathlib.Path(req.runtime_root).resolve() / req.run_id
    report_dir = run_dir / "upload"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.ndjson"

    completed = 0
    failed = 0
    processed = 0

    with report_path.open("a", encoding="utf-8") as report:
        for row in rows:
            processed += 1
            source_path = pathlib.Path(str(row.get("path", "")))
            artifact_type = str(row.get("artifact_type", "unknown"))
            step_id = str(row.get("step_id", "unknown"))
            size_bytes = int(row.get("size_bytes", 0))
            sha256 = str(row.get("sha256", ""))

            init_payload = {
                "run_id": req.run_id,
                "step_id": step_id,
                "artifact_type": artifact_type,
                "size_bytes": size_bytes,
                "sha256": sha256,
                "client_artifact_id": str(uuid.uuid4()),
            }

            item_report: dict[str, Any] = {
                "ts": _utc_iso(),
                "run_id": req.run_id,
                "source_path": str(source_path),
                "artifact_type": artifact_type,
                "step_id": step_id,
                "status": "unknown",
            }

            try:
                init_resp = client.init_artifact(init_payload)
                upload_url = str(init_resp.get("upload_url", ""))
                object_key = str(init_resp.get("object_key", source_path.name))

                if upload_url and not req.skip_object_upload:
                    _upload_binary(upload_url=upload_url, file_path=source_path)
                    item_report["upload_action"] = "uploaded"
                else:
                    item_report["upload_action"] = "skipped"

                complete_payload = {
                    "run_id": req.run_id,
                    "step_id": step_id,
                    "artifact_type": artifact_type,
                    "object_key": object_key,
                    "size_bytes": size_bytes,
                    "sha256": sha256,
                }
                complete_resp = client.complete_artifact(complete_payload)
                item_report["status"] = "completed"
                item_report["init_response"] = init_resp
                item_report["complete_response"] = complete_resp
                completed += 1
            except Exception as exc:  # noqa: BLE001
                item_report["status"] = "failed"
                item_report["error"] = str(exc)
                failed += 1

            report.write(json.dumps(item_report, ensure_ascii=False) + "\n")

    return UploadResult(
        run_id=req.run_id,
        manifest_path=str(manifest_path),
        processed=processed,
        completed=completed,
        failed=failed,
        report_path=str(report_path),
    )

