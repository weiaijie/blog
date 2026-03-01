# Codex CLI Auto Monitoring Dev

This folder is the implementation workspace for the step-by-step plan in:

- `/home/saber/projects/blog/codexcli-auto-monitoring-plan`

## Current development scope

- Step 01 (in progress): run initialization
  - Validate execution workspace
  - Detect platform (WSL/macOS/Windows/Linux)
  - Route by capability tags (including Windows desktop UI tasks)
  - Create `run_id` via API (or offline mode)
  - Persist `run.meta.json` and `run.env`

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

