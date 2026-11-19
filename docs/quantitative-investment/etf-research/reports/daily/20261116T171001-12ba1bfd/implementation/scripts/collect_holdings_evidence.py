"""Fetch selected official quarterly reports from an already captured SSE catalog."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,urllib.request,urllib.error

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);records=[];selected=[]
    for symbol in ('510300','511010'):
        catalog=ROOT/f'data/snapshots/2026-11-06-close-windows-1653/catalog_{symbol}.body'
        rows=[r for r in json.loads(catalog.read_text())['result'] if '2026年第3季度报告' in r['TITLE']]
        if len(rows)!=1:raise ValueError('Quarterly report selection is ambiguous')
        row=rows[0];path=row['URL']
        if not path.startswith('/disclosure/fund/announcement/') or not path.endswith('.pdf'):raise ValueError('Unexpected official path')
        url='https://www.sse.com.cn'+path
        selected.append(dict(symbol=symbol,title=row['TITLE'],announcement_date=row['SSEDATE'],url=url,catalog_sha256=hashlib.sha256(catalog.read_bytes()).hexdigest()))
        record=dict(name='quarterly_'+symbol,url=url,requested_at_utc=datetime.now(timezone.utc).isoformat())
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.sse.com.cn/'})
            with urllib.request.urlopen(req,timeout=25) as response:body=response.read();record.update(status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'))
        except urllib.error.HTTPError as e:body=e.read();record.update(status=e.code,error=str(e))
        except Exception as e:body=b'';record.update(error=type(e).__name__+': '+str(e))
        record.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),pdf_magic=body.startswith(b'%PDF-'))
        (a.output/(record['name']+'.pdf')).write_bytes(body);records.append(record)
    (a.output/'requests.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    (a.output/'selection.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
    (a.output/'collector.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.output.iterdir()) if p.is_file()},indent=2)+'\n')
    print(json.dumps(records,ensure_ascii=False))
    if any(r.get('status')!=200 or not r['pdf_magic'] for r in records):raise SystemExit(2)
if __name__=='__main__':main()
