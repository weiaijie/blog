"""Verify and restore the off-host record of scheduled ETF evidence exports."""
import argparse
import json
from pathlib import Path
from shutil import copytree

from etf_research.evidence_archive import safe_path
from etf_research.policy_events import instant
from etf_research.publication import read, sha
from pack_observation_evidence import merge_packs, restore_ledger, verify
from run_observation_export import BATCH, chain, verify_batch, verify_export_link

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'reports/research-observation-publication/catalog.json'


def audit(root, catalog, *, live_spool=None, destination=None):
    if catalog['schemaVersion'] != 1:
        raise ValueError('Unknown public observation catalog version')
    seed = safe_path(root,catalog['seed']['pack'])
    seed_sha = catalog['seed']['manifestSha256']
    if sha(safe_path(seed,'manifest.json')) != seed_sha:
        raise ValueError('Pinned public seed archive manifest changed')
    ceiling = instant(verify(seed)['asOf'])
    previous = seed_sha
    exported = []
    packs = [seed]
    for row in catalog['batches']:
        batch = row['batchId']
        if not BATCH.fullmatch(batch) or (exported and batch <= exported[-1][0]):
            raise ValueError('Public batch IDs must be unique and in chronological order')
        receipt_path = safe_path(root,row['receipt'])
        checksum = sha(receipt_path)
        if checksum != row['receiptSha256']:
            raise ValueError('Public batch receipt changed: '+batch)
        receipt = read(receipt_path)
        pack = safe_path(root,row['pack'])
        previous,ceiling = verify_export_link(pack,receipt,batch,previous,ceiling)
        verify_batch(pack,receipt)
        exported.append((batch,checksum))
        packs.append(pack)
    if catalog['head'] != dict(batchId=exported[-1][0] if exported else None,manifestSha256=previous):
        raise ValueError('Public catalog head does not match the verified chain')
    result = dict(schemaVersion=1,publishedBatchCount=len(exported),publishedThrough=ceiling.isoformat(),
                  publishedManifestSha256=previous,liveComparison=None)
    if live_spool is not None:
        live = chain(seed,seed_sha,live_spool,full=True)
        batches = live_spool/'batches'
        actual = sorted((path.name,sha(path/'receipt.json')) for path in batches.iterdir()) if batches.exists() else []
        if len(actual) != live['batchCount']:
            raise ValueError('Production export spool advanced during audit; retry after sealing')
        if actual[:len(exported)] != exported:
            raise ValueError('Public evidence is not the exact prefix of the production export chain')
        result['liveComparison'] = dict(sealedBatchCount=live['batchCount'],sealedThrough=live['through'],
                                        unpublishedBatchIds=[batch for batch,_ in actual[len(exported):]])
    if destination is not None:
        directory = destination.resolve()
        if any(directory.is_relative_to(pack.resolve()) for pack in packs):
            raise ValueError('Restore outside public evidence packs')
        directory.mkdir(parents=True,exist_ok=False)
        merged = directory/'pack'
        if len(packs) == 1:
            copytree(seed,merged)
        else:
            merge_packs(packs,merged)
        result['restored'] = restore_ledger(merged,directory/'ledger')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-spool',type=Path,help='Compare with the Ubuntu production export spool')
    parser.add_argument('--restore-to',type=Path,help='Recover a combined pack and ledger in a new directory')
    args = parser.parse_args()
    result = audit(ROOT,read(ROOT/CATALOG),live_spool=args.live_spool,destination=args.restore_to)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__ == '__main__':
    main()
