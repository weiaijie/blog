"""Controlled real-evidence replay; uses a separate pointer, never new returns."""
from pathlib import Path
from types import SimpleNamespace
from datetime import date
import argparse,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from etf_research.publication import create,read,sha,verify_bundle
from run_daily import run

def validate(folder):
    folder=folder.resolve();folder.relative_to(ROOT);folder.mkdir(parents=True,exist_ok=False)
    old=read(ROOT/'reports/2026-11-05-long-history/forward_checkpoint.json')
    pointer=folder/'active.json';create(pointer,dict(schema_version=1,as_of=old['as_of'],checkpoint='reports/2026-11-05-long-history/forward_checkpoint.json',checkpoint_sha256=old['checkpoint_sha256']))
    originals={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'reports').rglob('forward_checkpoint.json')}
    originals['reports/2026-11-06-intent/plan.json']=sha(ROOT/'reports/2026-11-06-intent/plan.json')
    a=SimpleNamespace(pointer=str(pointer.relative_to(ROOT)),through=date(2026,11,6),candidate='2026-11-06-close-windows-1653',official='2026-11-06-official-close-1650',resume=None,rebuild=False,retry_of=None,prepare_only=True)
    first=run(a);assert first['status']=='prepared'
    assert read(pointer)['as_of']=='2026-11-05'
    bundle=ROOT/first['bundle'];verify_bundle(bundle)
    prepared=read(bundle/'forward_checkpoint.json');expected=read(ROOT/'reports/2026-11-06-close/forward_checkpoint.json')
    assert prepared==expected
    a.resume=first['bundle'];promoted=run(a);assert promoted['status']=='published'
    repeat_resume=run(a);assert repeat_resume['status']=='already_published'
    a.resume=None;repeat=run(a);assert repeat['status']=='up_to_date'
    assert all(sha(ROOT/n)==value for n,value in originals.items())
    result=dict(replay_only=True,new_forward_observations=0,nov5_to_nov6_checkpoint_equal=True,prepare_preserved_pointer=True,first=first,promotion=promoted,repeated_resume=repeat_resume,repeated_daily=repeat,old_checkpoints_and_intent_unchanged=len(originals),reconciliation=read(bundle/'reconciliation.json'),intent_check=read(bundle/'intent_check.json'))
    create(folder/'validation.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('reconciliation','intent_check')},ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();validate(a.output)
