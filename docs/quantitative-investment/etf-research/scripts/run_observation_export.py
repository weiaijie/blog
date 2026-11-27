"""Seal incremental independent evidence at real service activation times."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from tempfile import mkdtemp

from pack_observation_evidence import export, verify
from etf_research.observation_slots import timer_identity
from etf_research.policy_events import instant
from etf_research.publication import create, lock, read, sha, sync_dir

ROOT=Path(__file__).resolve().parents[1]
TIMER='etf-research-observation-export.timer'
BATCH=re.compile(r'\d{8}T\d{12}Z-[0-9a-f]{8}')
EVIDENCE_ERRORS = (OSError,ValueError,KeyError,TypeError)


def check_spool(root,store,seed,spool):
    for source in (root,store,seed):
        if spool.is_relative_to(source) or source.is_relative_to(spool):
            raise ValueError('Export spool must be separate from the study, seed and archive')


def verify_batch(pack, receipt):
    batch = receipt['batchId']
    try:
        summary = verify(pack)
        if summary['receipts'] != receipt['receipts'] or summary['archives'] != receipt['archives']:
            raise ValueError('Pack does not match its export receipt')
    except EVIDENCE_ERRORS as error:
        raise ValueError(f'Exported batch {batch} failed verification: {error}') from error


def chain(seed, seed_sha, spool, *, full=False):
    if sha(seed/'manifest.json')!=seed_sha:
        raise ValueError('Pinned seed archive manifest changed')
    base=verify(seed)
    ceiling=instant(base['asOf'])
    previous=seed_sha
    latest=None
    count=0
    for batch in sorted((spool/'batches').iterdir()) if (spool/'batches').is_dir() else ():
        if not batch.is_dir() or batch.is_symlink() or not BATCH.fullmatch(batch.name):
            raise ValueError('Unexpected exported batch path')
        pack=batch/'pack'
        if any(path.is_symlink() for path in (pack,batch/'receipt.json',batch/'started.json',
                    pack/'manifest.json',pack/'index.json')):
            raise ValueError('Unexpected archive link')
        receipt=read(batch/'receipt.json')
        started=read(batch/'started.json')
        index=read(pack/'index.json')
        after=instant(receipt['after'])
        cutoff=instant(receipt['asOf'])
        packed=sha(pack/'manifest.json')
        trigger=receipt['trigger']
        if (receipt['schemaVersion']!=1 or receipt['batchId']!=batch.name
                or receipt['previousManifestSha256']!=previous or receipt['packManifestSha256']!=packed
                or not after==instant(index['after'])==ceiling
                or not after<cutoff==instant(index['asOf'])<=instant(receipt['sealedAt'])
                or trigger['unit']!=TIMER or not re.fullmatch('[a-f0-9]{32}',trigger['invocationId'])
                or batch.name!=identifier(cutoff,trigger)
                or started!={key:receipt[key] for key in ('asOf','after','trigger')}):
            raise ValueError('Broken export chain: '+batch.name)
        if full:
            verify_batch(pack,receipt)
        previous,ceiling,latest=packed,cutoff,receipt
        count+=1
    if latest is not None and not full:
        verify_batch(spool/'batches'/latest['batchId']/'pack',latest)
    return dict(schemaVersion=1,seedAsOf=base['asOf'],seedManifestSha256=seed_sha,
                batchCount=count,verifiedBatchCount=count if full else min(count,1),
                through=ceiling.isoformat(),manifestSha256=previous,latest=latest,
                stagedAttempts=sum(1 for _ in (spool/'staging').glob('*')))


def identifier(cutoff, trigger):
    return (cutoff.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            +'-'+trigger['invocationId'][:8])


def seal_export(root, store, seed, seed_sha, spool, cutoff, trigger):
    if trigger['unit']!=TIMER or not re.fullmatch('[a-f0-9]{32}',trigger['invocationId']):
        raise ValueError('Unverified export service invocation')
    check_spool(root,store,seed,spool)
    batch=identifier(cutoff,trigger)
    with lock(spool/'export.lock'):
        try:
            status=chain(seed,seed_sha,spool,full=True)
        except EVIDENCE_ERRORS as error:
            failure=spool/'audit-failures'/(batch+'.json')
            if not failure.exists():
                create(failure,dict(schemaVersion=1,asOf=cutoff.isoformat(),trigger=trigger,
                                    checkedAt=datetime.now(timezone.utc).isoformat(),
                                    errorType=type(error).__name__,error=str(error)[:1200]))
                sync_dir(failure.parent)
                sync_dir(spool)
            raise
        after=instant(status['through'])
        if cutoff<=after:
            return dict(status='already_covered',**status)
        if status['latest'] is not None and status['latest']['trigger']['invocationId']==trigger['invocationId']:
            return dict(status='already_sealed',**status)
        staging=spool/'staging'
        batches=spool/'batches'
        staging.mkdir(exist_ok=True)
        batches.mkdir(exist_ok=True)
        temp=Path(mkdtemp(prefix=batch+'-',dir=staging))
        create(temp/'started.json',dict(asOf=cutoff.isoformat(),after=after.isoformat(),trigger=trigger))
        result=export(root,store,temp/'pack',cutoff,after=after)
        packed=sha(temp/'pack/manifest.json')
        receipt=dict(schemaVersion=1,batchId=batch,after=after.isoformat(),asOf=cutoff.isoformat(),
                     sealedAt=datetime.now(timezone.utc).isoformat(),trigger=trigger,
                     previousManifestSha256=status['manifestSha256'],packManifestSha256=packed,
                     receipts=result['receipts'],archives=result['archives'])
        create(temp/'receipt.json',receipt)
        sync_dir(temp)
        target=batches/batch
        if target.exists():
            raise ValueError('An immutable batch already exists')
        temp.rename(target)
        sync_dir(staging)
        sync_dir(batches)
        sync_dir(spool)
        # Prior batches were checked under the same lock. Recheck the newly published batch.
        published=chain(seed,seed_sha,spool)
        published['verifiedBatchCount']+=status['verifiedBatchCount']
        return dict(status='sealed',**published)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--run',action='store_true')
    action.add_argument('--status',action='store_true',help='Check the chain and latest package')
    action.add_argument('--audit',action='store_true',help='Read and verify every package')
    parser.add_argument('--archive-store',required=True,type=Path)
    parser.add_argument('--seed',required=True,type=Path)
    parser.add_argument('--seed-manifest-sha256',required=True)
    parser.add_argument('--spool',required=True,type=Path)
    args=parser.parse_args()
    cutoff=datetime.now(timezone.utc)
    if args.spool.is_symlink():
        parser.error('Export spool must not be a symlink')
    store,seed,spool=(path.resolve() for path in (args.archive_store,args.seed,args.spool))
    check_spool(ROOT,store,seed,spool)
    if args.run:
        trigger=timer_identity(os.environ,TIMER)
        if trigger is None:
            parser.error('Scheduled export requires its own systemd timer')
        result=seal_export(ROOT,store,seed,args.seed_manifest_sha256,spool,cutoff,trigger)
    else:
        result=chain(seed,args.seed_manifest_sha256,spool,full=args.audit)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    main()
