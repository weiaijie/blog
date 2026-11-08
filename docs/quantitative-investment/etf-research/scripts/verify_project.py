"""Verify all immutable inputs and the latest report/code manifest; no network."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from etf_research.publication import inside,read,sha,verify_bundle
from etf_research.forward import digest,engine_digest
def verify(manifest,base):
 items=json.loads(manifest.read_text())
 for name,expected in items.items():
  p=base/name
  if not p.resolve().is_relative_to(base.resolve()):raise ValueError('Unsafe manifest path')
  if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError('Hash mismatch: '+str(p))
 return len(items)
def main():
 count=0;snapshots=list((ROOT/'data/snapshots').glob('*/manifest.json'))
 if not snapshots:raise ValueError('No source manifests')
 for m in snapshots:count+=verify(m,m.parent)
 report=ROOT/'reports/2026-11-08-position-delay/manifest.json';n=verify(report,ROOT)
 # These two live pointers are validated against immutable records, not an obsolete Git hash.
 active=read(ROOT/'config/active_run.json');state=read(inside(ROOT,active['checkpoint']))
 if digest({k:v for k,v in state.items() if k!='checkpoint_sha256'})!=state['checkpoint_sha256'] or state['engine_sha256']!=engine_digest() or state['real_money'] is not False:raise ValueError('Active checkpoint integrity failed')
 if active['checkpoint_sha256']!=state['checkpoint_sha256'] or active['as_of']!=state['as_of']:raise ValueError('Active pointer mismatch')
 bundle=inside(ROOT,active['bundle']);verify_bundle(bundle)
 if sha(bundle/'manifest.json')!=active['bundle_manifest_sha256']:raise ValueError('Active bundle mismatch')
 phase='not_recorded'
 if (ROOT/'site/operation_status.json').exists():
  status=read(ROOT/'site/operation_status.json');phase=status['phase'];operation=inside(ROOT,status['operation'])
  if phase=='running':read(operation/'started.json')
  elif phase in ('success','failed'):
   verify_bundle(operation)
   if read(operation/'result.json')!=status:raise ValueError('Live operation status differs from sealed record')
  else:raise ValueError('Unknown operation phase')
 if (ROOT/'site/health_status.json').exists():
  health=read(ROOT/'site/health_status.json');observation=inside(ROOT,health['observation']);verify_bundle(observation)
  if read(observation/'result.json')!=health:raise ValueError('Health status differs from sealed observation')
 print('PASS integrity:',len(snapshots),'source manifests /',count,'source files;',n,'immutable entries; account',active['as_of'],'operation phase',phase)
if __name__=='__main__':main()
