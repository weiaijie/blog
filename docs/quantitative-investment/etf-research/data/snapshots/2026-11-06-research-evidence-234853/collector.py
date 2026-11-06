from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys,json,subprocess
root=Path('/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research');sys.path.insert(0,str(root/'src'))
from etf_research.http_capture import fetch,load_policy,save_transport
from etf_research.publication import create,seal
folder=root/'data/snapshots'/datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-research-evidence-%H%M%S');folder.mkdir()
policy=load_policy(root/'config/collection.json');save_transport(folder,policy)
rows=[]
urls={'interim_510300':'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-08-29/510300_20260829_2Q86.pdf','interim_511010':'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-08-31/511010_20260831_XPI1.pdf','calendar_index':'https://www.sse.com.cn/disclosure/dealinstruc/closed/'}
for name,url in urls.items():
 row=fetch(folder,name,url,policy);rows.append(row)
 if name.startswith('interim_') and row.get('status')==200 and not row.get('error'):
  raw=folder/(name+'.body')
  if not raw.read_bytes().startswith(b'%PDF-'):raise ValueError('Not PDF')
  (folder/(name+'.pdf')).write_bytes(raw.read_bytes())
  subprocess.run(['pdftotext','-layout',str(raw),str(folder/(name+'.txt'))],check=True)
  result=subprocess.run(['pdfinfo',str(raw)],capture_output=True,text=True,check=True)
  (folder/(name+'_pdfinfo.txt')).write_text(result.stdout)
create(folder/'requests.json',rows)
(folder/'collector.py').write_bytes(Path(__file__).read_bytes());seal(folder)
print(json.dumps({'snapshot':folder.name,'responses':[{'name':r['name'],'status':r.get('status'),'error':r.get('error'),'bytes':r['bytes']} for r in rows]}))
