$ErrorActionPreference = 'Stop'
$pythonRuntime = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (-not (Test-Path -LiteralPath $pythonRuntime)) { $pythonRuntime = 'python' }
$env:PYTHONIOENCODING = 'utf-8'
& $pythonRuntime (Join-Path $PSScriptRoot 'app.py') @args
