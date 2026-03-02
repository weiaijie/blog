# Development Task Board

## Status

- `DONE` Step 01: Run initialization and routing
- `DONE` Step 02: Spawn `codex exec --json` with safe subprocess wiring
- `DONE` Step 03: Parse stdout/stderr and spool NDJSON locally
- `DONE` Step 04: Heartbeat loop and derived state machine
- `IN_PROGRESS` Step 05: Playwright pipeline and evidence artifacts
- `IN_PROGRESS` Step 06: Artifact upload (two-phase commit)
- `DONE` Step 07: Finalization and recovery replay
- `DONE` Step 08: Security baseline and deployment hardening
- `TODO` Step 09: Acceptance tests and load tests

## Step 01 checklist

- [x] Create implementation folder skeleton
- [x] Add task board and dev README
- [x] Implement platform detection and routing logic
- [x] Implement run creation client (API + offline mode)
- [x] Persist runtime metadata and env export file
- [x] Validate Step 01 via local command run
- [x] Freeze Step 01 outputs and start Step 02

## Step 02 checklist

- [x] Implement codex command builder
- [x] Implement subprocess launch wrapper with startup status check
- [x] Persist `process.meta.json` bootstrap metadata
- [x] Validate Step 02 with mock command and codex command
- [x] Start Step 03 stream parser

## Step 03 checklist

- [x] Implement local spool writer (`events.ndjson`)
- [x] Parse stdout JSON lines as `cli.jsonl`
- [x] Parse stderr lines as `cli.stderr`
- [x] Add CLI command to run local capture validation
- [x] Add batch sender to API `/v1/runs/{id}/events:batch`
- [x] Add retry + DLQ persistence for failed batches
- [x] Validate send path with `mock://` api base
- [x] Start Step 04 heartbeat loop + state derivation

## Step 04 checklist

- [x] Implement derived state logic (`RUNNER_OFFLINE/AI_IDLE/STALL_SUSPECTED/...`)
- [x] Persist heartbeat stream and current state snapshot
- [x] Add CLI command for heartbeat simulation
- [x] Integrate heartbeat loop with live process capture

## Step 05 checklist

- [x] Add automation step event envelope (`step.started/step.completed/step.failed`)
- [x] Generate artifact files and metadata manifest
- [x] Emit `artifact.created` events to spool
- [x] Add real Playwright runner command and artifact capture flow
- [ ] Validate Playwright run in environment with installed browser dependencies

## Step 06 checklist

- [x] Implement artifact init/complete API client methods
- [x] Implement manifest-driven upload pipeline
- [x] Persist upload report with per-artifact status
- [ ] Add object storage upload integration test against real presigned URL

## Step 07 checklist

- [x] Implement finalize logic (`run.completed/run.failed/run.aborted`)
- [x] Persist final summary and finished heartbeat
- [x] Implement startup replay scanner for spool files
- [x] Archive sent spool files after successful replay

## Step 08 checklist

- [x] Add log sanitization for stdout/stderr stream events
- [x] Redact common API key/token patterns in logged payloads
- [x] Add screenshot masking strategy for sensitive UI regions
- [x] Add security policy doc + operational checklist in dev workspace
