"""Rebuild the new audit into a temporary directory and compare every derived byte."""
from pathlib import Path
import json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]


def main():
    saved=ROOT/'reports/2026-11-06-research-audit'
    with tempfile.TemporaryDirectory(prefix='etf-horizon-reproduce-') as temp:
        output=Path(temp)/'report';output.mkdir();page=Path(temp)/'research-audit.html'
        for script in ('build_horizon_audit.py','check_horizon_audit.py','build_holdings_audit.py','check_calendar_readiness.py'):
            subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--output',str(output)],check=True,cwd=ROOT)
        subprocess.run([sys.executable,str(ROOT/'scripts/build_research_audit_page.py'),'--output',str(output),'--page',str(page)],check=True,cwd=ROOT)
        files=sorted(output.iterdir())
        for path in files:
            if path.read_bytes()!=(saved/path.name).read_bytes():raise AssertionError('Reproduction mismatch: '+path.name)
        if page.read_bytes()!=(ROOT/'site/research-audit.html').read_bytes():raise AssertionError('Page mismatch')
        result=dict(passed=True,derived_files_byte_identical=len(files),page_byte_identical=True,offline=True)
        (saved/'reproducibility.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
