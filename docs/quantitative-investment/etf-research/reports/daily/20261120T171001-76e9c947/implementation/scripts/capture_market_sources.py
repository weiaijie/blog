"""Capture public research-only HTTP requests from an explicit JSON list into a new snapshot."""
import argparse
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

def capture(jobs, out):
    names = [j['name'] for j in jobs]
    if len(set(names)) != len(names) or any(not re.fullmatch('[a-z0-9_]+', n) for n in names):
        raise ValueError('Invalid or repeated name')
    out.mkdir(parents=True, exist_ok=False)
    def request(job):
        name, url = job['name'], job['url']
        if urlsplit(url).scheme != 'https' or urlsplit(url).username:
            raise ValueError('Expected public HTTPS source')
        path = out/(name+'.body')
        start = datetime.now(timezone.utc).isoformat()
        args = ['curl','--disable','--silent','--show-error','--ipv4','--location','--proto','=https',
                '--proto-redir','=https','--connect-timeout','6','--max-time','24','--max-filesize','18000000',
                '--user-agent','Mozilla/5.0','--referer',job.get('referer',url),'--output',str(path),
                '--write-out','%{http_code} %{url_effective}']
        if 'post' in job:
            args.extend(['--header','Content-Type: '+job.get('type','application/x-www-form-urlencoded'),
                         '--data-raw',job['post']])
        result = subprocess.run(args+[url],capture_output=True)
        if not path.exists(): path.touch()
        meta = result.stdout.decode(errors='replace').split(maxsplit=1)
        return dict(**job,requested_at_utc=start,status=int(meta[0]) if meta else 0,
                    effective_url=meta[-1] if len(meta)>1 else url,exit_code=result.returncode,
                    error=result.stderr.decode(errors='replace'),bytes=path.stat().st_size,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with ThreadPoolExecutor(5) as pool: rows = list(pool.map(request,jobs))
    (out/'requests.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(out.iterdir())},indent=2)+'\n',encoding='utf-8')
    for r in rows: print(r['name'],r['status'],r['bytes'],r['exit_code'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jobs',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    capture(json.loads(a.jobs.read_text(encoding='utf-8-sig')),a.output)
