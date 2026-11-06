from pathlib import Path
import subprocess,sys
root=Path('/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research')
marker=Path('/tmp/etf-restart-acceptance-20261106.marker')
try:
 with marker.open('x') as f:f.write('Controlled first-start failure; no market or account mutation.\n')
 print('CONTROLLED_ACCEPTANCE_FAILURE_BEFORE_PIPELINE',flush=True)
 raise SystemExit(1)
except FileExistsError:
 print('CONTROLLED_RESTART_NOW_RUN_REAL_SUPERVISOR',flush=True)
 raise SystemExit(subprocess.run([sys.executable,str(root/'scripts/run_scheduled.py')],cwd=root).returncode)
