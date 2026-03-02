from __future__ import annotations

import asyncio
import hashlib
import json
import pathlib
from dataclasses import dataclass
from datetime import datetime, timezone

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
class PlaywrightRequest:
    run_id: str
    runtime_root: str
    url: str
    scenario: str = "playwright-flow"
    headless: bool = True
    timeout_ms: int = 30000
    mask_selectors: list[str] | None = None


@dataclass(frozen=True)
class PlaywrightResult:
    run_id: str
    scenario: str
    step_status: str
    manifest_path: str
    step_id: str
    error: str | None


async def _run(req: PlaywrightRequest) -> PlaywrightResult:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "playwright is not installed. Install dependency and run: python3 -m playwright install chromium"
        ) from exc

    run_dir = pathlib.Path(req.runtime_root).resolve() / req.run_id
    art_root = run_dir / "artifacts"
    ss_dir = art_root / "screenshots"
    vd_dir = art_root / "videos"
    tr_dir = art_root / "traces"
    for d in (ss_dir, vd_dir, tr_dir):
        d.mkdir(parents=True, exist_ok=True)

    spool = EventSpoolWriter(req.run_id, run_dir / "spool" / "events.ndjson")
    manifest_path = art_root / "manifest.ndjson"
    step_id = f"pw-{req.scenario}"
    step_status = "failed"
    error_msg: str | None = None
    screenshot_paths: list[pathlib.Path] = []

    spool.emit(
        source="automation",
        event_type="step.started",
        payload={"step_id": step_id, "scenario": req.scenario, "url": req.url},
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=req.headless)
        context = await browser.new_context(record_video_dir=str(vd_dir))
        page = await context.new_page()

        await context.tracing.start(screenshots=True, snapshots=True, sources=True)
        try:
            await page.goto(req.url, wait_until="domcontentloaded", timeout=req.timeout_ms)
            for selector in req.mask_selectors or []:
                loc = page.locator(selector)
                if await loc.count() > 0:
                    await loc.evaluate_all("els => els.forEach(e => e.style.filter = 'blur(10px)')")
            shot = ss_dir / f"{step_id}.png"
            await page.screenshot(path=str(shot), full_page=True)
            screenshot_paths.append(shot)
            step_status = "completed"
        except Exception as exc:  # noqa: BLE001
            error_msg = str(exc)
            shot = ss_dir / f"{step_id}-error.png"
            try:
                await page.screenshot(path=str(shot), full_page=True)
                screenshot_paths.append(shot)
            except Exception:
                pass
            step_status = "failed"
        finally:
            trace_path = tr_dir / f"{step_id}.zip"
            await context.tracing.stop(path=str(trace_path))
            await context.close()
            await browser.close()

    # Persist artifacts to manifest and events after browser closes
    artifact_paths: list[tuple[pathlib.Path, str]] = []
    for p in screenshot_paths:
        if p.exists():
            artifact_paths.append((p, "screenshot"))
    trace_path = tr_dir / f"{step_id}.zip"
    if trace_path.exists():
        artifact_paths.append((trace_path, "trace"))
    for video in vd_dir.glob("*.webm"):
        artifact_paths.append((video, "video"))

    with manifest_path.open("a", encoding="utf-8") as mf:
        for path, artifact_type in artifact_paths:
            item = {
                "schema_version": "1.0",
                "ts": _utc_iso(),
                "run_id": req.run_id,
                "step_id": step_id,
                "artifact_type": artifact_type,
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            mf.write(json.dumps(item, ensure_ascii=False) + "\n")
            spool.emit(source="automation", event_type="artifact.created", payload=item)

    payload = {"step_id": step_id, "scenario": req.scenario, "url": req.url}
    if error_msg:
        payload["error"] = error_msg
    spool.emit(source="automation", event_type=f"step.{step_status}", payload=payload)
    spool.close()

    return PlaywrightResult(
        run_id=req.run_id,
        scenario=req.scenario,
        step_status=step_status,
        manifest_path=str(manifest_path),
        step_id=step_id,
        error=error_msg,
    )


def run_playwright_automation(req: PlaywrightRequest) -> PlaywrightResult:
    return asyncio.run(_run(req))
