# Development Task Board

## Status

- `IN_PROGRESS` Step 01: Run initialization and routing
- `TODO` Step 02: Spawn `codex exec --json` with safe subprocess wiring
- `TODO` Step 03: Parse stdout/stderr and spool NDJSON locally
- `TODO` Step 04: Heartbeat loop and derived state machine
- `TODO` Step 05: Playwright pipeline and evidence artifacts
- `TODO` Step 06: Artifact upload (two-phase commit)
- `TODO` Step 07: Finalization and recovery replay
- `TODO` Step 08: Security baseline and deployment hardening
- `TODO` Step 09: Acceptance tests and load tests

## Step 01 checklist

- [x] Create implementation folder skeleton
- [x] Add task board and dev README
- [x] Implement platform detection and routing logic
- [x] Implement run creation client (API + offline mode)
- [x] Persist runtime metadata and env export file
- [ ] Validate Step 01 via local command run
- [ ] Freeze Step 01 outputs and start Step 02

