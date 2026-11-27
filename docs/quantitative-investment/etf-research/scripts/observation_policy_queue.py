"""Find exact official revisions and incomplete policy captures awaiting review."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from observation_status import archive_index, archived_bytes, production_paths
from policy_source_watch import article_url
from review_policy_observations import reviews_as_of, summarize_reviews
from etf_research.evidence_archive import safe_path
from etf_research.policy_events import instant
from etf_research.publication import read


def policy_inventory(store, receipt, record):
    coverage=record['coverage']
    if coverage is None:
        return None
    proof=coverage['evidence']['policyEtf']
    prefix=proof['path']+'/'
    if not prefix.startswith(receipt['attempt']+'/inputs/'):
        raise ValueError('Policy source differs from its archived attempt')
    identity=receipt['archive']
    archive=safe_path(store,f'snapshots/{identity}.json').read_bytes()
    if sha256(archive).hexdigest()!=identity:
        raise ValueError('Archive manifest changed')
    files=json.loads(archive)['files']
    manifest=files[prefix+'manifest.json']
    if manifest['sha256']!=proof['manifestSha256']:
        raise ValueError('Policy manifest reference changed')
    contents=json.loads(archived_bytes(store,manifest))
    result=files[prefix+'result.json']
    if contents['result.json']!=result['sha256']:
        raise ValueError('Policy result is outside the sealed capture')
    policy=json.loads(archived_bytes(store,result))['policy']
    if (policy['status']!=coverage['policy']['status']
            or len(policy['candidates'])!=coverage['policy']['candidateCount']):
        raise ValueError('Policy inventory differs from coverage')
    for row in policy['candidates']:
        name=row['evidence']
        if (article_url(row['index'],row['url'])!=row['url'] or not name.startswith('policy_') or '/' in name or '\\' in name or
                contents[name]!=row['sha256'] or files[prefix+name]['sha256']!=row['sha256'] or
                sha256((row['url']+'|'+row['sha256']).encode()).hexdigest()!=row['revisionKey'] or
                not instant(record['startedAt'])<=instant(row['receivedAt'])<=instant(receipt['archiveVerifiedAt'])):
            raise ValueError('Policy candidate could not be bound to its source')
    return policy


def queue(root, store, observed, *, draft=None):
    config=read(root/'config/research_observation.json')
    runs=root/'reports/research-observation/runs'
    if not runs.is_dir():
        raise FileNotFoundError('Independent observation attempt inventory is missing')
    entries,errors=archive_index(root,store,config,observed,days=sorted(
        path.name for path in runs.glob('????-??-??') if path.is_dir()))
    reviews=[review for _,review in reviews_as_of(root,store,observed)]
    review_summary=summarize_reviews(reviews,observed)
    reviewed={}
    checked_attempts=set()
    for review in sorted(reviews,key=lambda row:instant(row['sealedAt'])):
        checked_attempts.add(review['attempt'])
        for row in review['entries']:
            reviewed.setdefault(row['decision']['revisionKey'],row['decision'])
    seen,by_url={},{}
    incomplete,empty=[],[]
    complete_count=0
    draft_rows=None
    records=sorted((item for day in entries.values() for item in day),
                   key=lambda item:instant(item[0]['archiveVerifiedAt']))
    for receipt,record in records:
        attempt=receipt['attempt']
        detail=dict(attempt=attempt,archiveSha256=receipt['archive'],scheduled=receipt['trigger'] is not None,
                    archivedAt=receipt['archiveVerifiedAt'])
        try:
            policy=policy_inventory(store,receipt,record)
        except (OSError,ValueError,TypeError,KeyError):
            incomplete.append(dict(**detail,state='unverified',issues={}))
            continue
        if policy is None or policy['status']!='archived':
            incomplete.append(dict(**detail,state='capture_incomplete',
                                   issues=policy['issues'] if policy else record['errors']))
            continue
        complete_count+=1
        if not policy['candidates'] and attempt not in checked_attempts:
            empty.append(detail)
        if draft==attempt:
            draft_rows=policy['candidates']
        for item in policy['candidates']:
            key=item['revisionKey']
            prior=by_url.setdefault(item['url'],set())
            if key not in seen:
                seen[key]=dict(revisionKey=key,title=item['title'],url=item['url'],sha256=item['sha256'],
                               publishedAt=item['published_at'],receivedAt=item['receivedAt'],
                               firstSeen=detail,previousVersions=sorted(prior),appearances=0)
            prior.add(key)
            seen[key]['lastSeen']=detail
            seen[key]['appearances']+=1
    pending=[row for key,row in seen.items() if key not in reviewed]
    result=dict(schemaVersion=1,asOf=observed.isoformat(),completeCaptures=complete_count,
                observedRevisions=len(seen),reviewedRevisions=len(set(seen)&reviewed.keys()),
                pending=pending,emptyPending=empty,incompleteCaptures=incomplete,reviewSummary=review_summary,
                archiveIssues=[dict(day=day,**row) for day,issues in sorted(errors.items())
                               for row in issues])
    if draft is not None:
        if draft_rows is None:
            raise ValueError('Choose a completed policy capture visible at that cutoff')
        keys=[row['revisionKey'] for row in draft_rows]
        if len(set(keys))!=len(keys):
            raise ValueError('Duplicate policy revision in requested capture')
        result['draft']=dict(attempt=draft,reusedDecisions=[reviewed[key] for key in keys if key in reviewed],
                             requiresReview=[seen[key] for key in keys if key not in reviewed])
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    root,store=production_paths()
    parser.add_argument('--observation-root',type=Path,default=root)
    parser.add_argument('--archive-store',type=Path,default=store)
    parser.add_argument('--as-of',type=instant)
    parser.add_argument('--draft')
    options=parser.parse_args()
    now=datetime.now(timezone.utc)
    clock=options.as_of or now
    if clock>now:
        parser.error('Review cutoff cannot be in the future')
    result=queue(options.observation_root.resolve(),options.archive_store.resolve(),clock,draft=options.draft)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    main()
