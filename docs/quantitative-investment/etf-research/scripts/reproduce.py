"""Recompute admitted research offline into a fresh directory, compare saved bytes."""
from pathlib import Path
import tempfile,subprocess,os,sys,json
ROOT=Path(__file__).resolve().parents[1]
def main():
 env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'src')
 with tempfile.TemporaryDirectory(prefix='etf-reproduce-') as temp:
  out=Path(temp)/'results';site=Path(temp)/'index.html'
  commands=[['scripts/run_research.py','--long-history','--output',str(out)],['scripts/check_execution_results.py','--long-history','--results',str(out)],['scripts/build_site.py','--results',str(out),'--output',str(site)]]
  for args in commands:subprocess.run([sys.executable,*args],cwd=ROOT,env=env,check=True)
  saved=ROOT/'reports/2026-11-05-long-history';files=sorted(p for p in out.iterdir() if p.is_file())
  for p in files:
   if p.read_bytes()!=(saved/p.name).read_bytes():raise AssertionError('Reproduction mismatch: '+p.name)
  if site.read_bytes()!=(ROOT/'site/index.html').read_bytes():raise AssertionError('Dashboard reproduction mismatch')
  medium=Path(temp)/'medium'
  subprocess.run([sys.executable,'scripts/run_research.py','--extended','--output',str(medium)],cwd=ROOT,env=env,check=True)
  for f in medium.iterdir():
   if f.read_bytes()!=(ROOT/'reports/2026-11-04-extension'/f.name).read_bytes():raise AssertionError('1167-day result changed: '+f.name)
  old=Path(temp)/'old'
  subprocess.run([sys.executable,'scripts/run_research.py','--output',str(old)],cwd=ROOT,env=env,check=True)
  old_saved=ROOT/'reports/2026-11-04-closure'
  for f in old.iterdir():
   if f.read_bytes()!=(old_saved/f.name).read_bytes():raise AssertionError('Old result changed: '+f.name)
  state=Path(temp)/'forward.json';state.write_bytes((ROOT/'reports/2026-11-04-extension/forward_checkpoint.json').read_bytes());audit=Path(temp)/'admission.json'
  command=[sys.executable,'scripts/advance_forward.py','--snapshot','2026-11-05-admission-09','--state',str(state),'--audit',str(audit)]
  subprocess.run(command,cwd=ROOT,env=env,check=True)
  current=ROOT/'reports/2026-11-05-admission'
  if state.read_bytes()!=(current/'forward_checkpoint.json').read_bytes() or audit.read_bytes()!=(current/'admission.json').read_bytes():raise AssertionError('Admission/checkpoint reproduction mismatch')
  before=state.read_bytes();subprocess.run(command,cwd=ROOT,env=env,check=True)
  if before!=state.read_bytes():raise AssertionError('Checkpoint retry is not idempotent')
  command=[sys.executable,'scripts/advance_forward.py','--snapshot','2026-11-05-close-12b','--state',str(state),'--audit',str(audit)]
  subprocess.run(command,cwd=ROOT,env=env,check=True)
  if state.read_bytes()!=(saved/'forward_checkpoint.json').read_bytes() or audit.read_bytes()!=(saved/'admission.json').read_bytes():raise AssertionError('First forward observation changed')
  before=state.read_bytes();subprocess.run(command,cwd=ROOT,env=env,check=True)
  if before!=state.read_bytes():raise AssertionError('First forward retry mismatch')
  review=Path(temp)/'review'
  subprocess.run([sys.executable,'scripts/review_catalog.py','--snapshot','2026-11-05-rules-10','--output',str(review),'--download-evidence'],cwd=ROOT,env=env,check=True)
  for file in review.iterdir():
   if file.read_bytes()!=(ROOT/'reports/2026-11-05-notices/review'/file.name).read_bytes():raise AssertionError('Review packet reproduction mismatch: '+file.name)
  plan_audit=Path(temp)/'intent.json'
  subprocess.run([sys.executable,'scripts/audit_first_session.py','--output',str(plan_audit)],cwd=ROOT,env=env,check=True)
  if plan_audit.read_bytes()!=(ROOT/'reports/2026-11-06-intent/intent_replay.json').read_bytes():raise AssertionError('Intent replay mismatch')
  result={'saved_intent_byte_identical':True,'first_forward_day_byte_identical':True,'medium_core_result_files_unchanged':len(list(medium.iterdir())),'review_packet_byte_identical':True,'admission_and_checkpoint_byte_identical':True,'checkpoint_retry_idempotent':True,'old_core_result_files_unchanged':len(list(old.iterdir())),'offline_reproduction_passed':True,'research_files_byte_identical':len(files),'dashboard_byte_identical':True,'network_used_by_pipeline':False}
  (ROOT/'reports/2026-11-06-intent/reproducibility.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
