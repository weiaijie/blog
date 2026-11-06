from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys,json
root=Path('/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research');sys.path.insert(0,str(root/'src'))
from etf_research import http_capture
from etf_research.publication import create,seal
http_capture.HOSTS.add('bond.sse.com.cn')
folder=root/'data/snapshots'/datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-bond-identities-%H%M%S');folder.mkdir()
policy=http_capture.load_policy(root/'config/collection.json');http_capture.save_transport(folder,policy);rows=[]
for code in ['019793','019834','019829']:
 row=http_capture.fetch(folder,'bond_'+code,'https://bond.sse.com.cn/disclosure/info/index.shtml?BONDCODE='+code,policy);rows.append(row);create(folder/('bond_'+code+'_request.json'),row)
create(folder/'requests.json',rows);(folder/'collector.py').write_bytes(Path(__file__).read_bytes());seal(folder)
print(json.dumps({'snapshot':folder.name,'responses':[dict(name=r['name'],status=r.get('status'),bytes=r['bytes'],error=r.get('error')) for r in rows]}))
