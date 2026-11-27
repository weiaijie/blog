"""Prepare an append-only public release from verified scheduled evidence batches."""
import argparse
import json
from hashlib import sha256
from pathlib import Path
from shutil import copyfile

from audit_observation_repository import CATALOG, audit
from etf_research.evidence_archive import safe_path
from etf_research.policy_events import instant
from etf_research.publication import create, lock, read, sha
from pack_observation_evidence import put
from run_observation_export import verify_batch, verify_export_link

ROOT = Path(__file__).resolve().parents[1]
RELEASE_FOLDER = Path(CATALOG).parent


def prepare(project, spool, output, *, catalog_path=None):
    if not spool.is_dir() or spool.is_symlink():
        raise ValueError('Use the actual scheduled export spool directory')
    output = output.resolve()
    if output.is_relative_to(project.resolve()) or output.is_relative_to(spool.resolve()):
        raise ValueError('Prepare the release in a new directory outside both source trees')
    source_catalog = project/CATALOG if catalog_path is None else catalog_path
    source_bytes = source_catalog.read_bytes()
    catalog = json.loads(source_bytes)
    base_hash = sha256(source_bytes).hexdigest()
    with lock(spool/'export.lock'):
        status = audit(project,catalog,live_spool=spool)
        comparison = status['liveComparison']
        pending = comparison['unpublishedBatchIds']
        outcome = dict(schemaVersion=1,baseCatalogSha256=base_hash,unpublishedBatchIds=pending,
                       currentlyPublishedThrough=status['publishedThrough'])
        if not pending:
            return dict(outcome,status='up_to_date')
        if sha(source_catalog) != base_hash:
            raise ValueError('Public catalog changed during release preparation')
        output.mkdir(parents=True,exist_ok=False)
        rows = list(catalog['batches'])
        latest = status['publishedManifestSha256']
        through = instant(status['publishedThrough'])
        for batch_id in pending:
            batch = safe_path(spool,'batches/'+batch_id)
            relative = RELEASE_FOLDER/'batches'/batch_id
            target = output/relative
            source_pack = safe_path(batch,'pack')
            source_manifest = safe_path(source_pack,'manifest.json')
            target_pack = target/'pack'
            for name,digest in read(source_manifest).items():
                put(safe_path(source_pack,name),safe_path(target_pack,name),digest)
            copyfile(source_manifest,target_pack/'manifest.json')
            copyfile(safe_path(batch,'receipt.json'),target/'receipt.json')
            record = read(target/'receipt.json')
            latest,through = verify_export_link(target/'pack',record,batch_id,latest,through)
            verify_batch(target/'pack',record)
            rows.append(dict(batchId=batch_id,pack=(relative/'pack').as_posix(),
                             receipt=(relative/'receipt.json').as_posix(),receiptSha256=sha(target/'receipt.json')))
        if through != instant(comparison['sealedThrough']) or sha(source_catalog) != base_hash:
            raise ValueError('Verified preparation differs from the selected publication boundary')
        prepared = dict(catalog,batches=rows,head=dict(batchId=pending[-1],manifestSha256=latest))
        create(output/CATALOG,prepared)
        result = dict(outcome,status='prepared',preparedCatalogSha256=sha(output/CATALOG),
                      preparedThrough=through.isoformat(),preparedManifestSha256=latest)
        create(output/'preparation.json',result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spool',required=True,type=Path,help='Scheduled Ubuntu export spool')
    parser.add_argument('--output',required=True,type=Path,help='A separate, new staging directory')
    args = parser.parse_args()
    print(json.dumps(prepare(ROOT,args.spool,args.output),ensure_ascii=False,allow_nan=False))


if __name__ == '__main__':
    main()
