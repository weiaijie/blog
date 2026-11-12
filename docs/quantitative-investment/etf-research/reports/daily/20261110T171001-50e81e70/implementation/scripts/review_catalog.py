"""Create evidence packets or append review decisions; never approve admission."""
from pathlib import Path
import argparse, json, sys
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'src'))
from etf_research.notice_workflow import write_packet, save_decision
from etf_research.publication import read, lock

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--snapshot'); p.add_argument('--output', type=Path)
    p.add_argument('--download-evidence', action='store_true')
    p.add_argument('--packet'); p.add_argument('--decision', type=Path)
    a = p.parse_args()
    with lock(ROOT / '.runtime/review.lock'):
        if a.decision:
            if not a.packet or a.snapshot or a.output or a.download_evidence: p.error('Use --packet and --decision only')
            result = save_decision(ROOT, a.packet, read(a.decision))
        else:
            if not a.snapshot or not a.output or a.packet: p.error('--snapshot and --output required')
            packet = write_packet(ROOT, a.snapshot, a.output, a.download_evidence)
            requests = read(a.output / 'evidence_requests.json')
            result = dict(status=packet['status'], changes=len(packet['changes']), evidence_requests=len(requests), approves_prices_or_events=False)
            print(json.dumps(result, ensure_ascii=False))
            if any(r.get('error') or r.get('status') != 200 or not r['pdf_magic_valid'] for r in requests): raise SystemExit(2)
            return
        print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__': main()
