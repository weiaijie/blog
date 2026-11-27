"""Export dated independent research evidence and restore an original archive."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

from etf_research.evidence_archive import object_path, restore, safe_path, verify as verify_archive
from etf_research.exchange_calendar import BASE_PATH, REGISTRY
from etf_research.policy_events import instant
from etf_research.publication import create, read, seal, sha, verify_bundle

OBSERVATION = 'reports/research-observation'
REVIEW = 'reports/research-policy-reviews'
STAGES = ('decisions', 'opening', 'labels', 'models', 'forecasts', 'evaluation')
STAGE_PATHS = {f'reports/research-{stage}': stage for stage in STAGES}
STAGE_PATHS['reports/research-monthly-coverage'] = 'monthly'
OBSERVATION_RECEIPT = re.compile(fr'{OBSERVATION}/archives/(\d{{4}}-\d{{2}}-\d{{2}})/([a-zA-Z0-9-]+)\.json')
DYNAMIC = (OBSERVATION+'/runs/', *(name+'/' for name in STAGE_PATHS))
PUBLIC_FILES = {
    BASE_PATH, 'config/collection.json', 'config/research_observation.json',
    'PROTOCOL_OBSERVATION_V1.md',
}


def receipt_kind(name):
    if OBSERVATION_RECEIPT.fullmatch(name):
        return 'observation'
    parts = name.split('/')
    if parts[:2] == REVIEW.split('/') and len(parts) == 4 and parts[-1] == 'receipt.json':
        return 'policy_review'
    if len(parts) == 5 and parts[-1] == 'receipt.json' and '/'.join(parts[:2]) in STAGE_PATHS:
        return STAGE_PATHS['/'.join(parts[:2])]
    raise ValueError('Unrecognized research receipt: '+name)


def public_path(name):
    parts = Path(name).parts
    if any(part.startswith('.') for part in parts) or '__pycache__' in parts:
        raise ValueError('Private path in research evidence: '+name)
    if (name in PUBLIC_FILES or OBSERVATION_RECEIPT.fullmatch(name) or name.startswith((REGISTRY+'/',
            'data/snapshots/20261127T1605-official-etf-flow/', *DYNAMIC))
            and Path(name).suffix in ('.json', '.body', '.py', '.txt', '.headers', '.pdf', '.xml')):
        return
    if (re.fullmatch(r'(scripts|src/etf_research)/[a-z_0-9]+\.py',name)
            or re.fullmatch(r'deploy/etf-research-[a-z-]+\.(timer|service)',name)):
        return
    raise ValueError('Unexpected path in research archive: '+name)


def bound_snapshot(store, name, receipt, cutoff):
    kind = receipt_kind(name)
    ready = instant(receipt['sealedAt' if kind=='policy_review' else 'archiveVerifiedAt'])
    if ready > cutoff:
        raise ValueError('Receipt was published after the export cutoff')
    if kind == 'policy_review':
        return None, None
    if kind == 'observation':
        session,run = OBSERVATION_RECEIPT.fullmatch(name).groups()
        folder=f'{OBSERVATION}/runs/{session}/{run}'
        identity=receipt['archive']
        bindings={'manifest.json':receipt['attemptManifestSha256'],'result.json':receipt['resultSha256']}
        if receipt['session']!=session or receipt['attempt']!=folder:
            raise ValueError('Acquisition receipt path does not match')
    else:
        folder=name.removesuffix('/receipt.json')
        identity=receipt['archiveSha256']
        manifest_key='recordManifestSha256' if kind=='decisions' else 'manifestSha256'
        path_key='decisionPath' if kind=='decisions' else 'path'
        bindings={'records/manifest.json':receipt[manifest_key]}
        if receipt[path_key]!=folder:
            raise ValueError('Stage receipt path does not match')
    snapshot = verify_archive(store,identity)
    if not instant(snapshot['created_at_utc']) <= ready:
        raise ValueError('Archive timestamp exceeds receipt verification time')
    if any(snapshot['files'][f'{folder}/{key}']['sha256']!=digest for key,digest in bindings.items()):
        raise ValueError('Receipt does not match the verified archive')
    for archive_name in snapshot['files']:
        public_path(archive_name)
    return identity,snapshot


def put(source, destination, digest):
    if destination.exists():
        if sha(destination)!=digest:
            raise ValueError('Evidence already exists with different bytes')
        return
    destination.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as original, destination.open('xb') as target:
        shutil.copyfileobj(original,target)
    if sha(destination)!=digest:
        raise ValueError('Copy changed while reading evidence')


def review_files(source, receipt):
    parent=receipt.removesuffix('/receipt.json')+'/records'
    folder=safe_path(source,parent)
    verify_bundle(folder)
    result=read(safe_path(source,receipt))
    manifest=folder/'manifest.json'
    if sha(manifest)!=result['manifestSha256'] or set(read(manifest))!={'review.json'}:
        raise ValueError('Invalid policy review archive binding')
    return [parent+'/manifest.json',parent+'/review.json']


def copy_review(root, pack, name):
    for file in review_files(root,name):
        source=safe_path(root,file)
        put(source,safe_path(pack/'receipts',file),sha(source))


def export(root, store, pack, cutoff, after=None):
    root, store, pack = root.resolve(),store.resolve(),pack.resolve()
    if not (root/'config/research_observation.json').is_file() or not (store/'snapshots').is_dir():
        raise ValueError('Independent research root or archive store does not exist')
    if any(pack.is_relative_to(source) for source in (root,store)) or (after is not None and after>=cutoff):
        raise ValueError('Use a separate evidence destination and an increasing time interval')
    pack.mkdir(parents=True,exist_ok=False)
    paths=list((root/OBSERVATION/'archives').glob('*/*.json'))
    paths.extend((root/REVIEW).glob('*/receipt.json'))
    for stage in STAGE_PATHS:
        paths.extend((root/stage).glob('*/*/receipt.json'))
    rows=[]
    for path in sorted(paths):
        name=path.relative_to(root).as_posix()
        kind=receipt_kind(name)
        source=safe_path(root,name)
        receipt=read(source)
        ready=instant(receipt['sealedAt' if kind=='policy_review' else 'archiveVerifiedAt'])
        if ready>cutoff or (after is not None and ready<=after):
            continue
        identity,snapshot=bound_snapshot(store,name,receipt,cutoff)
        receipt_digest=sha(source)
        if read(source)!=receipt:
            raise ValueError('Receipt changed during export')
        put(source,safe_path(pack/'receipts',name),receipt_digest)
        if snapshot is None:
            copy_review(root,pack,name)
        else:
            archive=pack/'archive'
            leaf='snapshots/'+identity+'.json'
            put(safe_path(store,leaf),safe_path(archive,leaf),identity)
            for entry in snapshot['files'].values():
                digest=entry['sha256']
                put(object_path(store,digest),object_path(archive,digest),digest)
        rows.append(dict(receipt=name,kind=kind,sha256=receipt_digest,verifiedAt=ready.isoformat(),archive=identity))
    create(pack/'index.json',dict(schemaVersion=1,asOf=cutoff.isoformat(),
                                  after=after.isoformat() if after else None,receipts=rows))
    seal(pack)
    return verify(pack)


def verify(pack):
    verify_bundle(pack)
    index=read(pack/'index.json')
    if index['schemaVersion']!=1:
        raise ValueError('Unsupported independent research evidence version')
    cutoff=instant(index['asOf'])
    after=instant(index['after']) if index['after'] else None
    expected={'index.json'}
    archives=set()
    counts=Counter()
    for row in index['receipts']:
        name=row['receipt']
        relative='receipts/'+name
        kind=receipt_kind(name)
        path=safe_path(pack,relative)
        receipt=read(path)
        ready=instant(receipt['sealedAt' if kind=='policy_review' else 'archiveVerifiedAt'])
        if (relative in expected or kind!=row['kind'] or sha(path)!=row['sha256']
                or ready!=instant(row['verifiedAt']) or (after is not None and ready<=after)):
            raise ValueError('Receipt index or time range differs from sealed evidence')
        identity,snapshot=bound_snapshot(pack/'archive',name,receipt,cutoff)
        if row['archive']!=identity:
            raise ValueError('Archive identity differs from the export index')
        if snapshot is None:
            expected.update('receipts/'+file for file in review_files(pack/'receipts',name))
        else:
            archives.add(identity)
            expected.add('archive/snapshots/'+identity+'.json')
            expected.update(object_path(pack/'archive',entry['sha256']).relative_to(pack).as_posix()
                            for entry in snapshot['files'].values())
        expected.add(relative)
        counts[kind]+=1
    if set(read(pack/'manifest.json'))!=expected:
        raise ValueError('Export contains files outside its receipt inventory')
    return dict(asOf=index['asOf'],after=index['after'],receipts=dict(counts),archives=len(archives),
                files=len(expected))


def merge_packs(packs, output):
    """Join contiguous immutable exports without overwriting a receipt or object."""
    packs=[path.resolve() for path in packs]
    output=output.resolve()
    if len(packs)<2 or any(output.is_relative_to(pack) for pack in packs):
        raise ValueError('Use consecutive packs and a separate destination')
    rows=[]
    inventories={}
    previous=None
    lower=None
    for pack in packs:
        verify(pack)
        index=read(pack/'index.json')
        after=instant(index['after']) if index['after'] else None
        cutoff=instant(index['asOf'])
        if previous is None:
            lower=index['after']
        elif after!=previous or cutoff<=previous:
            raise ValueError('Evidence pack time intervals are not contiguous')
        previous=cutoff
        rows.extend(index['receipts'])
        for name,digest in read(pack/'manifest.json').items():
            if name=='index.json':
                continue
            existing=inventories.setdefault(name,(pack,digest))
            if existing[1]!=digest:
                raise ValueError('Portable evidence disagrees at path: '+name)
    if len({row['receipt'] for row in rows})!=len(rows):
        raise ValueError('A receipt occurs in more than one interval')
    output.mkdir(parents=True,exist_ok=False)
    for name,(pack,digest) in sorted(inventories.items()):
        put(safe_path(pack,name),safe_path(output,name),digest)
    create(output/'index.json',dict(schemaVersion=1,asOf=previous.isoformat(),after=lower,
                                    receipts=sorted(rows,key=lambda row:row['receipt'])))
    seal(output)
    return verify(output)


def separate_destination(pack, destination):
    if destination.resolve().is_relative_to(pack.resolve()):
        raise ValueError('Restore destination must be separate from the evidence package')


def restore_receipt(pack, name, destination):
    separate_destination(pack,destination)
    verify(pack)
    index=read(pack/'index.json')
    candidates=[row for row in index['receipts'] if row['receipt']==name]
    if len(candidates)!=1 or candidates[0]['archive'] is None:
        raise ValueError('Choose a receipt with an original content archive')
    row=candidates[0]
    source=safe_path(pack/'receipts',name)
    result=restore(pack/'archive',row['archive'],destination)
    put(source,safe_path(destination,name),row['sha256'])
    return dict(**result,receipt=name)


def restore_ledger(pack, destination):
    separate_destination(pack,destination)
    summary=verify(pack)
    index=read(pack/'index.json')
    archive=pack/'archive'
    records={}
    calendar={}
    for row in index['receipts']:
        identity=row['archive']
        if identity is None:
            continue
        snapshot=read(safe_path(archive,f'snapshots/{identity}.json'))
        created=instant(snapshot['created_at_utc'])
        for name,entry in snapshot['files'].items():
            digest=entry['sha256']
            if name.startswith(DYNAMIC):
                if records.setdefault(name,digest)!=digest:
                    raise ValueError('Archived ledger records disagree: '+name)
            elif (name in (BASE_PATH,'config/research_observation.json')
                  or name.startswith(REGISTRY+'/')):
                previous=calendar.get(name)
                if previous and previous[0]==created and previous[1]!=digest:
                    raise ValueError('Calendar version conflict at the same archive time')
                if previous is None or previous[0]<created:
                    calendar[name]=(created,digest)
    destination.mkdir(parents=True,exist_ok=False)
    files={**records,**{name:digest for name,(_,digest) in calendar.items()}}
    for name,digest in files.items():
        put(object_path(archive,digest),safe_path(destination,name),digest)
    receipts=safe_path(pack,'receipts')
    for path in sorted(receipts.rglob('*')):
        if path.is_file():
            relative=path.relative_to(receipts).as_posix()
            put(safe_path(receipts,relative),safe_path(destination,relative),sha(path))
    return dict(**summary,restoredArchiveFiles=len(files),activates_services=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='action',required=True)
    writer=commands.add_parser('export')
    writer.add_argument('--root',type=Path,required=True)
    writer.add_argument('--store',type=Path,required=True)
    writer.add_argument('--output',type=Path,required=True)
    writer.add_argument('--as-of',type=instant,required=True)
    writer.add_argument('--after',type=instant)
    checker=commands.add_parser('verify')
    checker.add_argument('--pack',type=Path,required=True)
    reader=commands.add_parser('restore')
    reader.add_argument('--pack',type=Path,required=True)
    reader.add_argument('--receipt',required=True)
    reader.add_argument('--destination',type=Path,required=True)
    ledger=commands.add_parser('restore-ledger')
    ledger.add_argument('--pack',type=Path,required=True)
    ledger.add_argument('--destination',type=Path,required=True)
    merger=commands.add_parser('merge')
    merger.add_argument('--pack',type=Path,action='append',required=True)
    merger.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.action=='export':
        if args.as_of>datetime.now(timezone.utc):
            parser.error('Export cutoff cannot be in the future')
        result=export(args.root,args.store,args.output,args.as_of,args.after)
    elif args.action=='verify':
        result=verify(args.pack)
    elif args.action=='restore':
        result=restore_receipt(args.pack,args.receipt,args.destination)
    elif args.action=='restore-ledger':
        result=restore_ledger(args.pack,args.destination)
    else:
        result=merge_packs(args.pack,args.output)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
