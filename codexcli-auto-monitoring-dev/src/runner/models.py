from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CapabilityRequest:
    requires_windows_ui: bool = False
    capabilities: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RunInitInput:
    prompt: str
    workdir: str
    runner_id: str
    machine_id: str
    api_base: str | None
    capability_request: CapabilityRequest
    runtime_root: str
    offline: bool = False


@dataclass(frozen=True)
class PlatformInfo:
    kind: str
    raw_platform: str
    is_wsl: bool


@dataclass(frozen=True)
class RouteDecision:
    route_target: str
    reason: str


@dataclass(frozen=True)
class RunInitResult:
    run_id: str
    stream_url: str | None
    route_target: str
    platform_kind: str
    warnings: list[str]
    meta_path: str
    env_path: str
    created_via_api: bool
    api_response: dict[str, Any]

