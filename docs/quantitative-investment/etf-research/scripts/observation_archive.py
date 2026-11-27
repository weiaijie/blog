"""Read-only verification of sealed observation attempts."""
import collect_policy_etf_day as etf
import collect_sse_research_day as sse
from run_research_observation import check_receipt
from etf_research.policy_events import instant
from etf_research.publication import inside, read, sha, verify_bundle


def archive_for_day(root, store, day, ceiling, config):
    source = root/'reports/research-observation'
    timely, late = [], 0
    for receipt_file in (source/'archives'/str(day)).glob('*.json'):
        raw = read(receipt_file)
        when = instant(raw['archiveVerifiedAt'])
        if when>ceiling:
            late += 1
            continue
        timely.append((when,receipt_file,raw))
    if not timely:
        return None,'archive_not_ready' if late else 'archive_missing'
    ignored = []
    for when, receipt_file, receipt in sorted(timely,reverse=True):
        folder = source/'runs'/str(day)/receipt_file.stem
        attempt = open_attempt(root,store,folder,config)
        if attempt is not None:
            if ignored:
                attempt['ignoredEmptyAttempts'] = ignored
            return attempt,None
        # The sealed inventory proves that this attempt carried no new source evidence.
        if (receipt['phase'] not in ('failed','interrupted')
                or set(read(folder/'manifest.json'))!={'started.json','result.json'}):
            break
        ignored.append(dict(attempt=receipt['attempt'],phase=receipt['phase'],
                            archiveVerifiedAt=when.isoformat(),archiveSha256=receipt['archive'],
                            receiptSha256=sha(receipt_file)))
    return None,'attempt_not_verified'


def open_attempt(root, store, folder, config):
    receipt = check_receipt(folder,store,config,root=root)
    day = folder.parent.name
    verify_bundle(folder)
    record = read(folder/'result.json')
    if record['coverage'] is None:
        return None
    captures = {}
    for label, verifier in (('policyEtf',etf.verify),('sse',sse.verify)):
        proof = record['coverage']['evidence'][label]
        path = inside(root,proof['path'])
        if not path.is_relative_to(folder/'inputs') or sha(path/'manifest.json')!=proof['manifestSha256']:
            raise ValueError('Unbound observation snapshot')
        captures[label] = verifier(path)
        if label=='policyEtf':
            policy_folder = path
        if captures[label]['date']!=str(day) or not instant(captures[label]['checkedAt'])<=instant(receipt['archiveVerifiedAt']):
            raise ValueError('Snapshot date or readiness differs from archived attempt')
    identity = receipt['archive']
    refs = [dict(root='observations',path=(folder/'manifest.json').relative_to(root).as_posix(),
                 sha256=receipt['attemptManifestSha256']),
            dict(root='archive',path='snapshots/'+identity+'.json',sha256=identity)]
    return dict(**captures,readyAt=receipt['archiveVerifiedAt'],refs=refs,trigger=receipt['trigger'],
                startedAt=record['startedAt'],id=folder.relative_to(root).as_posix(),policyFolder=policy_folder)
