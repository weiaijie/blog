# Codex CLI Auto Monitoring Dev

This folder is the implementation workspace for the step-by-step plan in:

- `/home/saber/projects/blog/codexcli-auto-monitoring-plan`

## Current development scope

- Step 01-04: implemented and locally validated
- Step 05-06: implemented with mock flow; real Playwright requires local dependency install
- Step 07: finalize and replay commands implemented
- Step 08: baseline sanitization and checklist implemented
- Step 09: acceptance/load test suite pending

## Quick start

```bash
cd /home/saber/projects/blog/codexcli-auto-monitoring-dev
python3 -m src.cli.main run-init \
  --prompt "scan project" \
  --workdir /home/saber/projects/blog \
  --offline
```

## Output

- `runtime/<run_id>/run.meta.json`
- `runtime/<run_id>/run.env`

## Step 02 quick check

```bash
cd /home/saber/projects/blog/codexcli-auto-monitoring-dev
python3 -m src.cli.main step02-launch \
  --run-id <run_id> \
  --prompt "step02 boot check" \
  --workdir /home/saber/projects/blog \
  --mock-command "python3 -c 'import time; print(\"ok\"); time.sleep(5)'"
```

Output:

- `runtime/<run_id>/process.meta.json`

## Step 03 quick check

```bash
cd /home/saber/projects/blog/codexcli-auto-monitoring-dev
python3 -m src.cli.main step03-capture \
  --run-id step03-sample \
  --workdir /home/saber/projects/blog
```

Output:

- `runtime/<run_id>/spool/events.ndjson`

Send to API:

```bash
cd /home/saber/projects/blog/codexcli-auto-monitoring-dev
python3 -m src.cli.main step03-send-batch \
  --run-id step03-sample \
  --api-base http://localhost:8000
```

If a batch fails after retries, it is persisted to:

- `runtime/<run_id>/dlq/events.batch.failed.ndjson`

Local mock send validation (no backend required):

```bash
python3 -m src.cli.main step03-send-batch \
  --run-id step03-sample \
  --api-base mock://local
```

## Step 04 quick check

```bash
cd /home/saber/projects/blog/codexcli-auto-monitoring-dev
python3 -m src.cli.main step04-heartbeat \
  --run-id step04-sample \
  --phase ai_running \
  --steps-done 1 \
  --steps-total 3 \
  --last-stdout-age 50 \
  --last-stderr-age 50 \
  --last-event-age 50 \
  --last-heartbeat-age 5 \
  --t-idle 45
```

Output:

- `runtime/<run_id>/heartbeat/heartbeat.ndjson`
- `runtime/<run_id>/heartbeat/state.json`

Live monitor loop (capture + heartbeat together):

```bash
python3 -m src.cli.main step04-live-monitor \
  --run-id step04-live \
  --workdir /home/saber/projects/blog
```

## Step 05 quick check (mock automation)

```bash
python3 -m src.cli.main step05-mock-automation \
  --run-id step05-sample \
  --scenario login-flow
```

Output:

- `runtime/<run_id>/artifacts/{screenshots,videos,traces}`
- `runtime/<run_id>/artifacts/manifest.ndjson`
- `runtime/<run_id>/spool/events.ndjson` (includes `step.*` and `artifact.created`)

Real Playwright run:

```bash
/home/saber/projects/blog/.venv/bin/python -m src.cli.main step05-playwright-run \
  --run-id step05-pw \
  --url https://example.com \
  --mask-selector "input[type='password']"
```

If missing dependencies:

- `python3 -m pip install playwright`
- `python3 -m playwright install chromium`

## Step 06 quick check (mock upload flow)

```bash
python3 -m src.cli.main step06-upload-artifacts \
  --run-id step05-sample \
  --api-base mock://local \
  --skip-object-upload
```

Output:

- `runtime/<run_id>/upload/report.ndjson`

## Step 07 quick check (finalize + replay)

```bash
python3 -m src.cli.main step07-finalize \
  --run-id step05-sample
```

```bash
python3 -m src.cli.main step07-replay \
  --api-base mock://local
```

Output:

- `runtime/<run_id>/final/run.final.json`
- `runtime/replay/report.ndjson`

## Security note

- stdout/stderr text is sanitized for common token/API key patterns before being written to spool.
