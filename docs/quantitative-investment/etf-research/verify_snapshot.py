from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent/'data/snapshots/2026-11-02'
manifest=json.loads((root/'manifest.json').read_text())
for name,expected in manifest.items():
    actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
    if actual!=expected:
        raise SystemExit('Hash mismatch: '+name)
print(f'PASS: {len(manifest)} snapshot files match SHA256 manifest')
