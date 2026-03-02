from __future__ import annotations

import argparse
import json
import pathlib
import socket
import sys

from src.runner.artifact_upload import UploadRequest, upload_artifacts
from src.runner.automation_pipeline import AutomationRequest, run_mock_automation
from src.runner.codex_exec import LaunchRequest, launch_codex_exec
from src.runner.event_sender import SendRequest, send_spool_events
from src.runner.finalize_replay import (
    FinalizeRequest,
    ReplayRequest,
    finalize_run,
    replay_spool_events,
)
from src.runner.heartbeat_state import HeartbeatRequest, write_heartbeat
from src.runner.live_monitor import LiveMonitorRequest, run_live_monitor
from src.runner.models import CapabilityRequest, RunInitInput
from src.runner.playwright_pipeline import PlaywrightRequest, run_playwright_automation
from src.runner.run_init import run_init
from src.runner.stream_capture import CaptureRequest, capture_streams


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codexcli-auto-monitoring-dev",
        description="Development CLI for Codex auto monitoring runner.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("run-init", help="Initialize run metadata and routing")
    p_init.add_argument("--prompt", required=True, help="User task prompt")
    p_init.add_argument("--workdir", required=True, help="Execution working directory")
    p_init.add_argument("--runner-id", default=socket.gethostname(), help="Logical runner id")
    p_init.add_argument("--machine-id", default=socket.gethostname(), help="Physical machine id")
    p_init.add_argument("--api-base", default=None, help="API base URL, e.g. http://localhost:8000")
    p_init.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_init.add_argument("--offline", action="store_true", help="Skip API request and create local run id")
    p_init.add_argument(
        "--requires-windows-ui",
        action="store_true",
        help="Route run to Windows desktop runner",
    )
    p_init.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Capability label (repeatable)",
    )

    p_launch = sub.add_parser("step02-launch", help="Launch codex exec process for Step 02")
    p_launch.add_argument("--run-id", required=True, help="Run id created by run-init")
    p_launch.add_argument("--prompt", required=True, help="Prompt passed to codex exec")
    p_launch.add_argument("--workdir", required=True, help="Execution working directory")
    p_launch.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_launch.add_argument("--startup-wait", type=float, default=1.0, help="Seconds to wait before status check")
    p_launch.add_argument("--no-full-auto", action="store_true", help="Disable --full-auto")
    p_launch.add_argument("--no-json", action="store_true", help="Disable --json")
    p_launch.add_argument("--skip-git-repo-check", action="store_true", help="Pass --skip-git-repo-check")
    p_launch.add_argument("--sandbox", default=None, help="Sandbox mode value")
    p_launch.add_argument("--output-last-message", default=None, help="Path for --output-last-message")
    p_launch.add_argument("--output-schema", default=None, help="Path for --output-schema")
    p_launch.add_argument("--mock-command", default=None, help="Use mock command instead of codex exec")
    p_launch.add_argument("--keep-alive", action="store_true", help="Do not terminate after startup check")

    p_capture = sub.add_parser("step03-capture", help="Capture stdout/stderr to local spool NDJSON")
    p_capture.add_argument("--run-id", required=True, help="Run id")
    p_capture.add_argument("--workdir", required=True, help="Execution working directory")
    p_capture.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_capture.add_argument("--capture-seconds", type=float, default=3.0, help="Capture duration before terminate")
    p_capture.add_argument(
        "--mock-command",
        default="python3 -c 'import json,sys,time; print(json.dumps({\"type\":\"thread.started\"})); print(\"progress...\", file=sys.stderr); time.sleep(1)'",
        help="Shell command used for local capture validation",
    )

    p_send = sub.add_parser("step03-send-batch", help="Send local spool events to API /events:batch")
    p_send.add_argument("--run-id", required=True, help="Run id")
    p_send.add_argument("--api-base", required=True, help="API base URL")
    p_send.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_send.add_argument("--spool-path", default=None, help="Override spool file path")
    p_send.add_argument("--batch-size", type=int, default=50, help="Events per batch")
    p_send.add_argument("--max-retries", type=int, default=3, help="Retries per batch")
    p_send.add_argument("--retry-base-seconds", type=float, default=0.5, help="Initial exponential backoff")

    p_hb = sub.add_parser("step04-heartbeat", help="Write heartbeat snapshot and derive run state")
    p_hb.add_argument("--run-id", required=True, help="Run id")
    p_hb.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_hb.add_argument(
        "--phase",
        default="ai_running",
        choices=["ai_running", "automation_running", "finalizing", "finished"],
        help="Current run phase",
    )
    p_hb.add_argument("--steps-done", type=int, default=0, help="Completed steps")
    p_hb.add_argument("--steps-total", type=int, default=0, help="Total steps")
    p_hb.add_argument("--cli-stopped", action="store_true", help="Mark cli as not alive")
    p_hb.add_argument("--last-stdout-age", type=float, default=0.0, help="Age in seconds")
    p_hb.add_argument("--last-stderr-age", type=float, default=0.0, help="Age in seconds")
    p_hb.add_argument("--last-event-age", type=float, default=0.0, help="Age in seconds")
    p_hb.add_argument("--last-heartbeat-age", type=float, default=0.0, help="Age in seconds")
    p_hb.add_argument("--t-dead", type=float, default=20.0, help="Offline threshold seconds")
    p_hb.add_argument("--t-idle", type=float, default=45.0, help="Idle threshold seconds")
    p_hb.add_argument("--t-stall", type=float, default=300.0, help="Stall threshold seconds")

    p_live = sub.add_parser("step04-live-monitor", help="Run capture + periodic heartbeat together")
    p_live.add_argument("--run-id", required=True, help="Run id")
    p_live.add_argument("--workdir", required=True, help="Execution working directory")
    p_live.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_live.add_argument("--duration-seconds", type=float, default=6.0, help="Max runtime before stop")
    p_live.add_argument("--heartbeat-interval", type=float, default=1.0, help="Heartbeat interval seconds")
    p_live.add_argument("--t-dead", type=float, default=20.0, help="Offline threshold seconds")
    p_live.add_argument("--t-idle", type=float, default=45.0, help="Idle threshold seconds")
    p_live.add_argument("--t-stall", type=float, default=300.0, help="Stall threshold seconds")
    p_live.add_argument(
        "--mock-command",
        default="python3 -c 'import json,sys,time; print(json.dumps({\"type\":\"thread.started\"})); print(\"progress-1\", file=sys.stderr); time.sleep(1); print(json.dumps({\"type\":\"item.completed\"})); print(\"progress-2\", file=sys.stderr); time.sleep(2)'",
        help="Shell command for live monitor validation",
    )

    p_auto = sub.add_parser("step05-mock-automation", help="Generate mock automation artifacts and events")
    p_auto.add_argument("--run-id", required=True, help="Run id")
    p_auto.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_auto.add_argument("--scenario", default="default", help="Scenario label")
    p_auto.add_argument("--fail", action="store_true", help="Emit step.failed instead of step.completed")

    p_pw = sub.add_parser("step05-playwright-run", help="Run real Playwright automation and collect artifacts")
    p_pw.add_argument("--run-id", required=True, help="Run id")
    p_pw.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_pw.add_argument("--url", required=True, help="Target URL")
    p_pw.add_argument("--scenario", default="playwright-flow", help="Scenario label")
    p_pw.add_argument("--timeout-ms", type=int, default=30000, help="Navigation timeout milliseconds")
    p_pw.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    p_pw.add_argument(
        "--mask-selector",
        action="append",
        default=[],
        help="CSS selector to blur before screenshot (repeatable)",
    )

    p_up = sub.add_parser("step06-upload-artifacts", help="Upload artifacts from manifest (init/complete flow)")
    p_up.add_argument("--run-id", required=True, help="Run id")
    p_up.add_argument("--api-base", required=True, help="API base URL or mock://local")
    p_up.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_up.add_argument("--manifest-path", default=None, help="Override manifest path")
    p_up.add_argument(
        "--skip-object-upload",
        action="store_true",
        help="Skip binary PUT to upload_url; still call init/complete",
    )

    p_fin = sub.add_parser("step07-finalize", help="Finalize run status and emit terminal event")
    p_fin.add_argument("--run-id", required=True, help="Run id")
    p_fin.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_fin.add_argument("--canceled", action="store_true", help="Force run.aborted")
    p_fin.add_argument("--canceled-reason", default=None, help="Optional reason for abort")

    p_replay = sub.add_parser("step07-replay", help="Replay spool events to API and archive successful spools")
    p_replay.add_argument("--runtime-root", default="runtime", help="Runtime output root")
    p_replay.add_argument("--api-base", required=True, help="API base URL or mock://local")
    p_replay.add_argument("--run-id", default=None, help="Only replay a single run id")
    p_replay.add_argument("--no-archive", action="store_true", help="Do not archive sent spool files")
    p_replay.add_argument("--batch-size", type=int, default=50, help="Batch size")
    p_replay.add_argument("--max-retries", type=int, default=3, help="Retries per batch")
    return parser


def _read_env_file(runtime_root: str, run_id: str) -> dict[str, str]:
    env_path = pathlib.Path(runtime_root).resolve() / run_id / "run.env"
    if not env_path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def cmd_run_init(args: argparse.Namespace) -> int:
    inputs = RunInitInput(
        prompt=args.prompt,
        workdir=args.workdir,
        runner_id=args.runner_id,
        machine_id=args.machine_id,
        api_base=args.api_base,
        capability_request=CapabilityRequest(
            requires_windows_ui=bool(args.requires_windows_ui),
            capabilities=list(args.capability),
        ),
        runtime_root=args.runtime_root,
        offline=bool(args.offline),
    )
    result = run_init(inputs)
    out = {
        "run_id": result.run_id,
        "platform_kind": result.platform_kind,
        "route_target": result.route_target,
        "created_via_api": result.created_via_api,
        "stream_url": result.stream_url,
        "warnings": result.warnings,
        "meta_path": result.meta_path,
        "env_path": result.env_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step02_launch(args: argparse.Namespace) -> int:
    env_overrides = _read_env_file(runtime_root=args.runtime_root, run_id=args.run_id)
    req = LaunchRequest(
        run_id=args.run_id,
        prompt=args.prompt,
        workdir=args.workdir,
        full_auto=not bool(args.no_full_auto),
        json_mode=not bool(args.no_json),
        skip_git_repo_check=bool(args.skip_git_repo_check),
        sandbox=args.sandbox,
        output_last_message=args.output_last_message,
        output_schema=args.output_schema,
        startup_wait_seconds=float(args.startup_wait),
        terminate_after_check=not bool(args.keep_alive),
        mock_command=args.mock_command,
        env_overrides=env_overrides,
    )
    result = launch_codex_exec(req=req, runtime_root=args.runtime_root)
    out = {
        "run_id": result.run_id,
        "pid": result.pid,
        "command": result.command,
        "started_at": result.started_at,
        "initial_status": result.initial_status,
        "initial_returncode": result.initial_returncode,
        "final_returncode": result.final_returncode,
        "process_meta_path": result.process_meta_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step03_capture(args: argparse.Namespace) -> int:
    command = ["bash", "-lc", args.mock_command]
    req = CaptureRequest(
        run_id=args.run_id,
        workdir=args.workdir,
        command=command,
        runtime_root=args.runtime_root,
        capture_seconds=float(args.capture_seconds),
    )
    result = capture_streams(req)
    out = {
        "run_id": result.run_id,
        "command": result.command,
        "returncode": result.returncode,
        "total_events": result.total_events,
        "stdout_events": result.stdout_events,
        "stderr_events": result.stderr_events,
        "spool_path": result.spool_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step03_send_batch(args: argparse.Namespace) -> int:
    spool_path = args.spool_path
    if not spool_path:
        spool_path = f"{args.runtime_root}/{args.run_id}/spool/events.ndjson"

    req = SendRequest(
        run_id=args.run_id,
        spool_path=spool_path,
        api_base=args.api_base,
        runtime_root=args.runtime_root,
        batch_size=int(args.batch_size),
        max_retries=int(args.max_retries),
        retry_base_seconds=float(args.retry_base_seconds),
    )
    result = send_spool_events(req)
    out = {
        "run_id": result.run_id,
        "spool_path": result.spool_path,
        "total_read": result.total_read,
        "total_sent": result.total_sent,
        "failed_batches": result.failed_batches,
        "parse_errors": result.parse_errors,
        "dlq_path": result.dlq_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step04_heartbeat(args: argparse.Namespace) -> int:
    req = HeartbeatRequest(
        run_id=args.run_id,
        runtime_root=args.runtime_root,
        cli_alive=not bool(args.cli_stopped),
        phase=args.phase,
        steps_done=int(args.steps_done),
        steps_total=int(args.steps_total),
        last_stdout_age_seconds=float(args.last_stdout_age),
        last_stderr_age_seconds=float(args.last_stderr_age),
        last_event_age_seconds=float(args.last_event_age),
        last_heartbeat_age_seconds=float(args.last_heartbeat_age),
        t_dead_seconds=float(args.t_dead),
        t_idle_seconds=float(args.t_idle),
        t_stall_seconds=float(args.t_stall),
    )
    result = write_heartbeat(req)
    out = {
        "run_id": result.run_id,
        "derived_state": result.derived_state,
        "runner_online": result.runner_online,
        "cli_alive": result.cli_alive,
        "phase": result.phase,
        "steps_done": result.steps_done,
        "steps_total": result.steps_total,
        "heartbeat_path": result.heartbeat_path,
        "state_path": result.state_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step04_live_monitor(args: argparse.Namespace) -> int:
    req = LiveMonitorRequest(
        run_id=args.run_id,
        workdir=args.workdir,
        command=["bash", "-lc", args.mock_command],
        runtime_root=args.runtime_root,
        duration_seconds=float(args.duration_seconds),
        heartbeat_interval_seconds=float(args.heartbeat_interval),
        t_dead_seconds=float(args.t_dead),
        t_idle_seconds=float(args.t_idle),
        t_stall_seconds=float(args.t_stall),
    )
    result = run_live_monitor(req)
    out = {
        "run_id": result.run_id,
        "returncode": result.returncode,
        "total_events": result.total_events,
        "stdout_events": result.stdout_events,
        "stderr_events": result.stderr_events,
        "spool_path": result.spool_path,
        "heartbeat_path": result.heartbeat_path,
        "final_state": result.final_state,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step05_mock_automation(args: argparse.Namespace) -> int:
    req = AutomationRequest(
        run_id=args.run_id,
        runtime_root=args.runtime_root,
        scenario=args.scenario,
        fail=bool(args.fail),
    )
    result = run_mock_automation(req)
    out = {
        "run_id": result.run_id,
        "scenario": result.scenario,
        "step_status": result.step_status,
        "screenshot_path": result.screenshot_path,
        "video_path": result.video_path,
        "trace_path": result.trace_path,
        "manifest_path": result.manifest_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step05_playwright_run(args: argparse.Namespace) -> int:
    req = PlaywrightRequest(
        run_id=args.run_id,
        runtime_root=args.runtime_root,
        url=args.url,
        scenario=args.scenario,
        headless=not bool(args.headed),
        timeout_ms=int(args.timeout_ms),
        mask_selectors=list(args.mask_selector),
    )
    result = run_playwright_automation(req)
    out = {
        "run_id": result.run_id,
        "scenario": result.scenario,
        "step_id": result.step_id,
        "step_status": result.step_status,
        "manifest_path": result.manifest_path,
        "error": result.error,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step06_upload_artifacts(args: argparse.Namespace) -> int:
    manifest_path = args.manifest_path
    if not manifest_path:
        manifest_path = f"{args.runtime_root}/{args.run_id}/artifacts/manifest.ndjson"
    req = UploadRequest(
        run_id=args.run_id,
        manifest_path=manifest_path,
        api_base=args.api_base,
        runtime_root=args.runtime_root,
        skip_object_upload=bool(args.skip_object_upload),
    )
    result = upload_artifacts(req)
    out = {
        "run_id": result.run_id,
        "manifest_path": result.manifest_path,
        "processed": result.processed,
        "completed": result.completed,
        "failed": result.failed,
        "report_path": result.report_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step07_finalize(args: argparse.Namespace) -> int:
    req = FinalizeRequest(
        run_id=args.run_id,
        runtime_root=args.runtime_root,
        canceled=bool(args.canceled),
        canceled_reason=args.canceled_reason,
    )
    result = finalize_run(req)
    out = {
        "run_id": result.run_id,
        "final_status": result.final_status,
        "final_event_type": result.final_event_type,
        "final_path": result.final_path,
        "heartbeat_state_path": result.heartbeat_state_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_step07_replay(args: argparse.Namespace) -> int:
    req = ReplayRequest(
        runtime_root=args.runtime_root,
        api_base=args.api_base,
        run_id=args.run_id,
        archive_sent=not bool(args.no_archive),
        batch_size=int(args.batch_size),
        max_retries=int(args.max_retries),
    )
    result = replay_spool_events(req)
    out = {
        "scanned_runs": result.scanned_runs,
        "sent_runs": result.sent_runs,
        "failed_runs": result.failed_runs,
        "report_path": result.report_path,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run-init":
            return cmd_run_init(args)
        if args.command == "step02-launch":
            return cmd_step02_launch(args)
        if args.command == "step03-capture":
            return cmd_step03_capture(args)
        if args.command == "step03-send-batch":
            return cmd_step03_send_batch(args)
        if args.command == "step04-heartbeat":
            return cmd_step04_heartbeat(args)
        if args.command == "step04-live-monitor":
            return cmd_step04_live_monitor(args)
        if args.command == "step05-mock-automation":
            return cmd_step05_mock_automation(args)
        if args.command == "step05-playwright-run":
            return cmd_step05_playwright_run(args)
        if args.command == "step06-upload-artifacts":
            return cmd_step06_upload_artifacts(args)
        if args.command == "step07-finalize":
            return cmd_step07_finalize(args)
        if args.command == "step07-replay":
            return cmd_step07_replay(args)
        parser.error(f"unsupported command: {args.command}")
        return 2
    except Exception as exc:  # noqa: BLE001
        err = {
            "error": str(exc),
            "command": args.command,
        }
        print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
