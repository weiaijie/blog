"""Verify all immutable inputs and the latest report/code manifest; no network."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
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
 report=ROOT/'reports/2026-11-06-engine-matrix-final/manifest.json';n=verify(report,ROOT)
 print('PASS:',len(snapshots),'source manifests /',count,'source files;',n,'current report, code and input-manifest entries')
if __name__=='__main__':main()
