from __future__ import annotations

import os
import pathlib
import sys

from .models import CapabilityRequest, PlatformInfo, RouteDecision


def detect_platform() -> PlatformInfo:
    raw = sys.platform

    if raw == "darwin":
        return PlatformInfo(kind="macos", raw_platform=raw, is_wsl=False)

    if raw.startswith("linux"):
        if os.environ.get("WSL_DISTRO_NAME"):
            return PlatformInfo(kind="wsl", raw_platform=raw, is_wsl=True)
        proc_version = pathlib.Path("/proc/version")
        if proc_version.exists():
            text = proc_version.read_text(encoding="utf-8", errors="ignore").lower()
            if "microsoft" in text or "wsl" in text:
                return PlatformInfo(kind="wsl", raw_platform=raw, is_wsl=True)
        return PlatformInfo(kind="linux", raw_platform=raw, is_wsl=False)

    if raw.startswith("win"):
        return PlatformInfo(kind="windows", raw_platform=raw, is_wsl=False)

    return PlatformInfo(kind="unknown", raw_platform=raw, is_wsl=False)


def validate_workdir(workdir: str, platform_kind: str) -> list[str]:
    p = pathlib.Path(workdir).resolve()
    warnings: list[str] = []

    if not p.exists():
        raise ValueError(f"workdir does not exist: {p}")
    if not p.is_dir():
        raise ValueError(f"workdir is not a directory: {p}")
    if not os.access(p, os.R_OK):
        raise ValueError(f"workdir is not readable: {p}")

    if platform_kind in {"wsl", "macos", "linux", "windows"} and not os.access(p, os.X_OK):
        warnings.append(f"workdir may not be executable/searchable: {p}")
    if platform_kind in {"wsl", "macos", "linux", "windows"} and not os.access(p, os.W_OK):
        warnings.append(f"workdir is not writable (may be intentional for read-only runs): {p}")

    # High I/O workloads are slower on /mnt/* in WSL.
    if platform_kind == "wsl" and str(p).startswith("/mnt/"):
        warnings.append("WSL workdir is under /mnt/*; high I/O steps may be slower and less stable.")

    return warnings


def choose_route(capability_request: CapabilityRequest, platform: PlatformInfo) -> RouteDecision:
    if capability_request.requires_windows_ui:
        return RouteDecision(
            route_target="windows_desktop_runner",
            reason="requires_windows_ui=true",
        )

    if platform.kind in {"wsl", "macos", "linux", "windows"}:
        return RouteDecision(
            route_target="local_runner",
            reason=f"default route for platform={platform.kind}",
        )

    raise ValueError(f"unsupported platform for local runner: {platform.raw_platform}")

