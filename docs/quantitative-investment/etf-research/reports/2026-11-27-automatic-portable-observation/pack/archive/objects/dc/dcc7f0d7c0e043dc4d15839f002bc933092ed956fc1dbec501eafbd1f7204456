"""Replay-based checkpoint continuation for an independently admitted Dataset.

Never fetches or admits raw inputs. Existing loader remains the admission gate.
A checkpoint is an audit record; balances are rebuilt, not blindly deserialized.
"""
from pathlib import Path
from dataclasses import replace
from datetime import date,datetime,time,timedelta
from zoneinfo import ZoneInfo
import hashlib,json
from .baselines import run,STRATEGIES,SCENARIOS
START=date(2026,11,5)
PROTOCOL='0c797f5ed5321d8653d64ccf0f795e1529f6f9b2'
def encode(value):return json.dumps(value,default=str,sort_keys=True,separators=(',',':'))
def digest(value):return hashlib.sha256(encode(value).encode()).hexdigest()
def engine_digest():
 root=Path(__file__).parent
 return digest({n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['forward.py','baselines.py','accounting.py','data.py']})
def prefix_digest(data,as_of):
 return digest({'sessions':[d for d in data.sessions if d<=as_of],'bars':{s:[vars(v[d]) for d in data.sessions if d<=as_of] for s,v in data.bars.items()},'events':[vars(e) for e in data.dividends if e.announcement_date<=as_of]})
def advance(data,previous=None,*,now=None):
 """Only close data eligible at 16:00 Asia/Shanghai, plus upstream admission.

 Day-completion time is a conservative processing rule, NOT proof of finality.
 Prefix revisions and engine changes require an explicit new audit branch.
 """
 now=now or datetime.now(ZoneInfo('Asia/Shanghai'))
 if now.tzinfo is None:raise ValueError('Timezone-aware current time required')
 local=now.astimezone(ZoneInfo('Asia/Shanghai'))
 cutoff=local.date() if local.time()>=time(16) else local.date()-timedelta(days=1)
 sessions=tuple(day for day in data.sessions if day<=cutoff)
 if not sessions:raise ValueError('No admitted completed sessions')
 as_of=sessions[-1];engine=engine_digest()
 if previous is not None:
  signed={k:v for k,v in previous.items() if k!='checkpoint_sha256'}
  if digest(signed)!=previous.get('checkpoint_sha256'):raise ValueError('Checkpoint checksum mismatch')
  if previous.get('protocol_commit')!=PROTOCOL or previous.get('engine_sha256')!=engine:raise ValueError('Protocol/engine changed; explicit review required')
  old=date.fromisoformat(previous['as_of'])
  if old>as_of:raise ValueError('Cannot roll checkpoint backward')
  if prefix_digest(data,old)!=previous['admitted_prefix_sha256']:raise ValueError('Historical input revision; review before resuming')
 clipped=replace(data,sessions=sessions,bars={s:{d:v[d] for d in sessions} for s,v in data.bars.items()},dividends=tuple(e for e in data.dividends if e.announcement_date<=as_of))
 portfolios={}
 if as_of>=START:
  if START not in sessions:raise ValueError('Missing protocol start session; no silent late start')
  for strategy in STRATEGIES:
   for scenario in SCENARIOS:
    name=strategy+'_'+scenario;r=run(clipped,strategy,scenario,account_start=START)
    portfolios[name]=json.loads(encode(r))
 # Verify previous calculated history as well as its input fingerprint.
 if previous is not None and previous.get('portfolios'):
  old=previous['as_of']
  for name,prior in previous['portfolios'].items():
   current=portfolios[name]
   for key,field in [('daily','date'),('journal','day'),('decisions','day')]:
    if [r for r in current[key] if r[field]<=old]!=prior[key]:raise ValueError('Previously published account history changed')
 checkpoint={'format':1,'protocol_commit':PROTOCOL,'engine_sha256':engine,'as_of':str(as_of),'forward_start':str(START),'admitted_prefix_sha256':prefix_digest(data,as_of),'status':'pending_future_observations' if not portfolios else 'research_account_active','forward_sessions':sum(d>=START for d in sessions),'portfolios':portfolios,'real_money':False}
 checkpoint['checkpoint_sha256']=digest(checkpoint)
 return checkpoint
