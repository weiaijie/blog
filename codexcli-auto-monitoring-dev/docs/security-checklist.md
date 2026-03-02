# Security Checklist

## Runtime and secrets

- Do not hardcode `CODEX_API_KEY` in source code.
- Inject secrets via environment or secret manager only.
- Ensure `run.env` does not contain long-lived secrets.

## Logging and events

- stdout/stderr lines are sanitized before writing to spool.
- Redact token/API key patterns from text payloads.
- Avoid writing full sensitive prompts/credentials into command logs.

## Artifacts

- Treat screenshots/videos/traces as sensitive by default.
- Restrict access to artifact storage bucket/path.
- Define retention and deletion policy for artifacts and logs.

## Windows desktop runner

- Require interactive desktop session for UI capture tasks.
- Keep Windows runner isolated from general-purpose workloads.
- Route only `requires_windows_ui=true` tasks to Windows desktop nodes.

## Operational controls

- Alert on repeated replay failures (DLQ growth).
- Alert on runner offline state crossing `T_dead`.
- Keep an audit trail for permission/sandbox level used per run.

