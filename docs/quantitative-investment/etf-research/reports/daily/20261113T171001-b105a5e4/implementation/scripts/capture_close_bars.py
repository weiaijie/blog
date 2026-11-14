"""Pin public ES series and retain exact source lines for the selected research dates."""
import argparse
import csv
import gzip
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from urllib.request import urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REV = 'b8f2d8ab36e44c289036ce093bf7c9f04073a7d9'
FILES = [
    (3,'raw/ES/3min/ES_3min_2024-01-01_2025-12-19_tradingview-chart.csv','a77b04622e75ea0e4f53508d531bf9052b59ce4a'),
    (1,'raw/ES/1min/ES_1min_2025-06-20_2026-10-09_alfordlabs-gh.csv.gz','665debfd7284ffc0f17fd80f8064df017dacb54c'),
]


def capture(out):
    with (ROOT/'reports/2026-11-08-nav-fx/market.csv').open() as f:
        days={r['date'] for r in csv.DictReader(f) if r['symbol']=='513500' and (
            D(r['premium_pct'])>5 or '2024-12-16'<=r['date']<='2025-04-07')}
    out.mkdir(parents=True,exist_ok=False)
    requests=[]
    for minutes,path,oid in FILES:
        url=f'https://raw.githubusercontent.com/kfccolonel1/BARS/{REV}/{path}'
        now=datetime.now(timezone.utc).isoformat()
        with urlopen(url,timeout=60) as r:
            raw=r.read()
            if r.status!=200 or r.geturl()!=url:
                raise ValueError('Unbound response')
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=oid:
            raise ValueError('Pinned source blob differs')
        requests.append(dict(url=url,requested_at_utc=now,status=200,source_blob=oid,bytes=len(raw),
                             sha256=hashlib.sha256(raw).hexdigest(),excerpt_minutes=minutes))
        stream=gzip.decompress(raw) if path.endswith('.gz') else raw
        offset=0
        with (out/f'rows_{minutes}m.jsonl').open('x',encoding='utf8',newline='\n') as f:
            for line in stream.splitlines(keepends=True):
                pos=offset
                offset+=len(line)
                if not line[:1].isdigit():
                    continue
                text=line.decode('ascii')
                opening=datetime.fromisoformat(text.partition(',')[0])
                if opening.tzinfo is None:
                    if minutes!=1 or not stream.startswith(b'# alfordlabs symbol=ES kind=future pv=50 tick=0.25 bars=1min tz=America/New_York'):
                        raise ValueError('Unzoned ES bar')
                    opening=opening.replace(tzinfo=ZoneInfo('America/New_York'))
                end=opening+timedelta(minutes=minutes)
                if (end.date().isoformat() in days and end.minute==0 and end.second==0 and
                        (end.astimezone(timezone.utc).hour==7 or end.hour in (13,16))):
                    f.write(json.dumps(dict(uncompressed_offset=pos,raw_line=text))+'\n')
    (out/'requests.json').write_text(json.dumps(requests,indent=2)+'\n',encoding='utf8')
    (out/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(out.iterdir())},indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    capture(p.parse_args().output)
