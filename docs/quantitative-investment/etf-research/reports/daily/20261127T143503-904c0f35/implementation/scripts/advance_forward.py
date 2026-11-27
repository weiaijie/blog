"""Safely update a local research checkpoint from admitted data, no network."""
from pathlib import Path
import argparse,json,os,tempfile
from etf_research.data import load_dataset
from etf_research.forward import advance
from etf_research.admission import load_incremental
p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--extended',action='store_true');p.add_argument('--snapshot');p.add_argument('--audit',type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[1]
if a.snapshot:data,audit=load_incremental(root/'data/snapshots',a.snapshot)
else:data=load_dataset(root/'data/snapshots',extended=a.extended);audit=None
old=json.loads(a.state.read_text()) if a.state.exists() else None
result=advance(data,old)
a.state.parent.mkdir(parents=True,exist_ok=True)
fd,tmp=tempfile.mkstemp(prefix='.forward-',dir=a.state.parent)
try:
 with os.fdopen(fd,'w') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,a.state)
finally:
 if os.path.exists(tmp):os.unlink(tmp)
if a.audit is not None and audit is not None:
 a.audit.parent.mkdir(parents=True,exist_ok=True);a.audit.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','as_of','forward_sessions','checkpoint_sha256']},ensure_ascii=False))
