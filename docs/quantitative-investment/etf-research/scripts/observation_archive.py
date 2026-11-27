"""Read-only verification of sealed observation attempts."""
from hashlib import sha256
import collect_policy_etf_day as etf
import collect_sse_research_day as sse
from run_research_observation import check_receipt
from etf_research.evidence_archive import verify as verify_archive
from etf_research.policy_events import instant
from etf_research.publication import inside, read, sha, verify_bundle


PURE_TRANSPORT = {6,7,28,52,55,56}
EMPTY_SHA = sha256(b'').hexdigest()


def archive_for_day(root, store, day, ceiling, config, *, recover_transport=False):
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
    newest_first = sorted(timely,reverse=True)
    for index, (when, receipt_file, receipt) in enumerate(newest_first):
        folder = source/'runs'/str(day)/receipt_file.stem
        attempt = open_attempt(root,store,folder,config)
        if attempt is not None:
            if recover_transport and index+1<len(newest_first):
                prior_receipt = newest_first[index+1][1]
                recovered = retry_recoveries(root,store,folder,receipt_file,attempt,prior_receipt,config)
                if recovered:
                    attempt['transportRecoveries'] = recovered
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



def pure_transport(folder, row):
    """A response-free retry is not a replacement publication or a withdrawal."""
    tries = row.get('attempts',[])
    names = [f"{row['name']}_attempt_{i:02d}" for i in range(1,len(tries)+1)]
    if not names or row.get('selected_attempt')!=names[-1] or [r['name'] for r in tries]!=names:
        return False
    return all(
        record['status']==0 and record['curl_exit'] in PURE_TRANSPORT
        and record['bytes']==0 and record['sha256']==EMPTY_SHA
        and record['url']==record['final_url']==row['url']
        and (raw := folder/(record['name']+'.body')).is_file() and sha(raw)==EMPTY_SHA
        for record in [row,*tries]
    )


def request_groups(root, folder, attempt, *, missing_only):
    evidence = read(folder/'result.json')['coverage']['evidence']
    specs = {}
    for label in ('policyEtf','sse'):
        packet = attempt[label]
        source = inside(root,evidence[label]['path'])
        run = read(source/'run.json')
        rows = {r['name']:r for r in read(source/'requests.json')}
        day,prior = (run[k].replace('-','') for k in ('date','previousDate'))
        if label=='policyEtf':
            for fund in packet['etf']:
                value = fund['relativeIntensity']
                if (value is None)!=missing_only:
                    continue
                symbol = fund['symbol']
                navs = ('nav_510300',) if symbol=='510300' else (
                    'nav_511010_'+day,'nav_511010_'+(run['followingDate'] or '').replace('-',''))
                names = ['shares_'+day,'shares_'+prior,'catalog_'+symbol,*navs]
                if all(name in rows for name in names):
                    specs[symbol] = (value,packet['receivedAt'],fund['featureReadyAt'],
                                     {name:rows[name] for name in names},source)
        else:
            turnover = 'market_'+day
            debt = packet['margin']
            margin = debt['financingBuyShare'] if debt is not None else None
            for name,value,names in (
                ('turnover',packet['turnoverCny'],[turnover]),
                ('margin',margin,[turnover,'margin',*(k for k in rows if k.startswith('detail_'+day+'_'))]),
            ):
                if (value is None)==missing_only:
                    specs[name] = (value,packet['receivedAt'],packet['featureReadyAt'],
                                   {key:rows[key] for key in names},source)
    return specs


def retry_recoveries(root, store, folder, receipt, current, prior_receipt, config):
    newer = request_groups(root,folder,current,missing_only=True)
    missing = {name:sorted(key for key,row in rows.items() if pure_transport(source,row))
               for name,(_,_,_,rows,source) in newer.items()}
    if not any(missing.values()):
        return {}
    earlier = folder.parent/prior_receipt.stem
    try:
        previous = open_attempt(root,store,earlier,config)
        if previous is None:
            return {}
        older = request_groups(root,earlier,previous,missing_only=False)
    except (OSError,ValueError,KeyError,TypeError,ArithmeticError):
        # Inability to verify an optional fallback must not erase unrelated current inputs.
        return {}
    used = {}
    for name,keys in missing.items():
        if not keys or name not in older:
            continue
        value,received,ready,original,_ = older[name]
        rows = newer[name][3]
        if original.keys()!=rows.keys() or any(
                not etf.usable(old) or old['url']!=rows[key]['url']
                or key not in keys and (not etf.usable(rows[key]) or old['sha256']!=rows[key]['sha256'])
                for key,old in original.items()):
            continue
        proofs = [*previous['refs'],*current['refs']]
        proofs.extend(dict(root='observations',path=path.relative_to(root).as_posix(),sha256=sha(path))
                      for path in (prior_receipt,receipt))
        used[name] = dict(value=value,receivedAt=received,readyAt=previous['readyAt'],
                          dependencyReadyAt=[ready,previous['readyAt'],current['readyAt']],
                          refs=proofs,failedRequests=keys,usedAttempt=previous['id'],retryAttempt=current['id'])
    if used:
        try:
            for path in (prior_receipt,receipt):
                verify_archive(store,read(path)['archive'])
        except (OSError,ValueError,KeyError,TypeError):
            return {}
    return used
