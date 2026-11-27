"""Archive dated Bosera PCFs, preserving original bytes and public Last-Modified headers."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

PREFIX = '2026-11-08-close-timing-0603'


def capture(root, out):
    paths = [root/(PREFIX+'a/pcf_example.body'),*sorted((root/(PREFIX+'b')).glob('pcf_*.body'))]
    jobs = []
    for path in paths:
        html = path.read_text(encoding='utf8')
        day = re.search(r'最新公告日期</th>\s*<td>(\d{4})年(\d{2})月(\d{2})日</td>',html)
        links = re.findall(r'href="(/jjcp/etf/files/513500/[^"]+\.(?:ETF|xml))"',html)
        if day is None or len(links)!=1:
            raise ValueError('Ambiguous daily PCF: '+path.name)
        jobs.append((''.join(day.groups()),'https://www.bosera.com'+links[0]))
    if len(dict(jobs))!=len(jobs):
        raise ValueError('Duplicate day')
    out.mkdir(parents=True,exist_ok=False)
    def fetch(job):
        day,url = job
        now = datetime.now(timezone.utc).isoformat()
        with tempfile.TemporaryDirectory() as work:
            hdr,body = Path(work)/'headers',Path(work)/'body'
            r=subprocess.run(['curl','--disable','-sS','--proto','=https','--max-time','18',
                              '--connect-timeout','5','--max-filesize','2000000','-D',str(hdr),'-o',str(body),
                              '-w','%{http_code}',url],capture_output=True)
            raw = body.read_bytes() if body.exists() else b''
            headings = dict((k.lower(),v.strip()) for k,sep,v in
                            (l.partition(':') for l in hdr.read_text(encoding='latin1').splitlines()) if sep)
            record = dict(day=day,url=url,requested_at_utc=now,status=int(r.stdout or '0'),exit_code=r.returncode,
                          last_modified=headings.get('last-modified'),etag=headings.get('etag'),
                          error=r.stderr.decode(errors='replace'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            return record,raw
    rows=[]
    with ThreadPoolExecutor(5) as pool, ZipFile(out/'responses.zip','x',compression=ZIP_DEFLATED) as archive:
        for record,raw in pool.map(fetch,jobs):
            archive.writestr(record['day']+'.body',raw)
            rows.append(record)
    (out/'requests.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(out.iterdir())},indent=2)+'\n')
    print('Archived',len(rows),'dated PCF responses')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--snapshots',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    capture(a.snapshots,a.output)
