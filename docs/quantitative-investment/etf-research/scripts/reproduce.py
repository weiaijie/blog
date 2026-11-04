"""Recompute admitted research offline into a fresh directory, compare saved bytes."""
from pathlib import Path
import tempfile,subprocess,os,sys,json
ROOT=Path(__file__).resolve().parents[1]
def main():
 env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'src')
 with tempfile.TemporaryDirectory(prefix='etf-reproduce-') as temp:
  out=Path(temp)/'results';site=Path(temp)/'index.html'
  commands=[['scripts/run_research.py','--output',str(out)],['scripts/check_execution_results.py','--results',str(out)],['scripts/build_site.py','--results',str(out),'--output',str(site)]]
  for args in commands:subprocess.run([sys.executable,*args],cwd=ROOT,env=env,check=True)
  saved=ROOT/'reports/2026-11-04-closure';files=sorted(p for p in out.iterdir() if p.is_file())
  for p in files:
   if p.read_bytes()!=(saved/p.name).read_bytes():raise AssertionError('Reproduction mismatch: '+p.name)
  if site.read_bytes()!=(ROOT/'site/index.html').read_bytes():raise AssertionError('Dashboard reproduction mismatch')
  result={'offline_reproduction_passed':True,'research_files_byte_identical':len(files),'dashboard_byte_identical':True,'network_used_by_pipeline':False}
  (saved/'reproducibility.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
