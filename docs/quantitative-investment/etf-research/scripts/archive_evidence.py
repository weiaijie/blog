"""Explicit archive/verify/restore/compare; never merges or activates a restored copy."""
from pathlib import Path
import argparse, json, sys
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'src'))
from etf_research.evidence_archive import capture, verify, restore, compare

def main():
    p=argparse.ArgumentParser(); p.add_argument('action', choices=['capture','verify','restore','compare'])
    p.add_argument('--store', type=Path, required=True); p.add_argument('--snapshot'); p.add_argument('--destination', type=Path)
    p.add_argument('--compress-manifest',action='store_true',help='Store a new archive manifest as gzip')
    a=p.parse_args()
    if a.compress_manifest and a.action!='capture': p.error('--compress-manifest is only valid for capture')
    if a.action=='capture':
        result=capture(ROOT,a.store,compress_manifest=a.compress_manifest)
    else:
        if not a.snapshot: p.error('--snapshot required')
        if a.action=='verify': result=dict(snapshot=a.snapshot,verified_files=len(verify(a.store,a.snapshot)['files']))
        else:
            if not a.destination: p.error('--destination required')
            result=(restore if a.action=='restore' else compare)(a.store,a.snapshot,a.destination)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
