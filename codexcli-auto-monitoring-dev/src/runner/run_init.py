from __future__ import annotations

import json
import pathlib
import socket
import uuid
from datetime import datetime, timezone
from typing import Any

from .api_client import RunApiClient, create_offline_run
from .models import RunInitInput, RunInitResult
from .platform import choose_route, detect_platform, validate_workdir


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_capabilities(capabilities: list[str]) -> list[str]:
    items = sorted({c.strip() for c in capabilities if c.strip()})
    return items


def _resolve_run_id(api_response: dict[str, Any]) -> str:
    for key in ("run_id", "id"):
        if key in api_response and api_response[key]:
            return str(api_response[key])
    return str(uuid.uuid4())


def _write_runtime_files(runtime_root: pathlib.Path, run_id: str, meta: dict[str, Any]) -> tuple[pathlib.Path, pathlib.Path]:
    run_dir = runtime_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    meta_path = run_dir / "run.meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    env_path = run_dir / "run.env"
    env_lines = [
        f"RUN_ID={run_id}",
        f"RUNNER_ID={meta['runner']['runner_id']}",
        f"ROUTE_TARGET={meta['route']['route_target']}",
        f"WORKDIR={meta['workdir']}",
    ]
    env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    return meta_path, env_path


def run_init(inputs: RunInitInput) -> RunInitResult:
    platform = detect_platform()
    warnings = validate_workdir(inputs.workdir, platform.kind)
    route = choose_route(inputs.capability_request, platform)
    capabilities = _normalize_capabilities(inputs.capability_request.capabilities)

    payload: dict[str, Any] = {
        "prompt": inputs.prompt,
        "workdir": str(pathlib.Path(inputs.workdir).resolve()),
        "runner": {
            "runner_id": inputs.runner_id or socket.gethostname(),
            "machine_id": inputs.machine_id or socket.gethostname(),
            "platform": platform.kind,
            "raw_platform": platform.raw_platform,
        },
        "routing": {
            "requires_windows_ui": inputs.capability_request.requires_windows_ui,
            "capabilities": capabilities,
            "route_target": route.route_target,
            "route_reason": route.reason,
        },
        "requested_at": _utc_iso(),
    }

    if inputs.offline or not inputs.api_base:
        api_response = create_offline_run(payload)
        created_via_api = False
    else:
        client = RunApiClient(inputs.api_base)
        api_response = client.create_run(payload)
        created_via_api = True

    run_id = _resolve_run_id(api_response)
    stream_url = api_response.get("stream_url")

    runtime_root = pathlib.Path(inputs.runtime_root).resolve()
    runtime_root.mkdir(parents=True, exist_ok=True)

    meta: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": run_id,
        "created_at": _utc_iso(),
        "workdir": str(pathlib.Path(inputs.workdir).resolve()),
        "runner": payload["runner"],
        "route": payload["routing"],
        "warnings": warnings,
        "stream_url": stream_url,
        "created_via_api": created_via_api,
        "api_response": api_response,
    }
    meta_path, env_path = _write_runtime_files(runtime_root, run_id, meta)

    return RunInitResult(
        run_id=run_id,
        stream_url=stream_url,
        route_target=route.route_target,
        platform_kind=platform.kind,
        warnings=warnings,
        meta_path=str(meta_path),
        env_path=str(env_path),
        created_via_api=created_via_api,
        api_response=api_response,
    )

