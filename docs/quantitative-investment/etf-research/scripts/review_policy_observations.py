"""Seal explicit review decisions against the exact official candidate bytes."""
import argparse
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import re

from observation_archive import open_attempt
from etf_research.policy_events import append_source_version, instant, select_as_of
from etf_research.publication import create, inside, read, seal, sha, verify_bundle

STAGES = {'deployment','details','implementation','progress','adjustment'}
ROLES = {'original','government_reprint'}
IDENTITY = re.compile('[a-z0-9]+(?:-[a-z0-9]+)*')
HASH = re.compile('[a-f0-9]{64}')


class BodyText(HTMLParser):
    def __init__(self, raw):
        super().__init__()
        self.parts = []
        self.hidden = None
        self.feed(raw.decode('utf-8-sig'))
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'):
            self.hidden = tag

    def handle_endtag(self, tag):
        if tag==self.hidden:
            self.hidden = None

    def handle_data(self, data):
        if self.hidden is None:
            self.parts.append(data)


def compact(text):
    return ''.join(text.split())


def reviewable_capture(capture):
    return capture['status']=='archived' or (
        capture['status']=='coverage_incomplete' and bool(capture['candidates']))


def build_review(root, store, requested, *, completed_at=None):
    config = read(root/'config/research_observation.json')
    folder = inside(root,requested['attempt'])
    runs = root/'reports/research-observation/runs'
    if not folder.is_relative_to(runs) or len(folder.relative_to(runs).parts)!=2:
        raise ValueError('Policy review must bind an observation attempt')
    attempt = open_attempt(root,store,folder,config)
    if attempt is None:
        raise ValueError('Policy capture unavailable')
    capture = attempt['policyEtf']['policy']
    if not reviewable_capture(capture):
        raise ValueError('No verified policy candidates in the incomplete capture')
    candidates = {c['revisionKey']:c for c in capture['candidates']}
    decisions = {d['revisionKey']:d for d in requested['decisions']}
    if (len(candidates)!=len(capture['candidates']) or len(decisions)!=len(requested['decisions'])
            or decisions.keys()!=candidates.keys()):
        raise ValueError('Every archived candidate revision must be reviewed exactly once')
    entries = []
    seen = {}
    for key, candidate in candidates.items():
        decision = decisions[key]
        if not HASH.fullmatch(key) or not decision['reason'].strip() or not decision['locator'].strip():
            raise ValueError('Policy classification requires an evidence locator and reason')
        path = inside(attempt['policyFolder'],candidate['evidence'])
        if sha(path)!=candidate['sha256'] or compact(decision['locator']) not in compact(
                ''.join(BodyText(path.read_bytes()).parts)):
            raise ValueError('Review evidence does not match candidate body')
        state = decision['disposition']
        if state=='event':
            ids = (decision['eventId'],decision['themeId'])
            if (not all(IDENTITY.fullmatch(value) for value in ids)
                    or decision['stage'] not in STAGES or decision['role'] not in ROLES):
                raise ValueError('Event classification incomplete')
            definition = (decision['themeId'],decision['stage'])
            if seen.setdefault(ids[0],definition)!=definition:
                raise ValueError('Conflicting event theme or stage')
        elif state=='related_followup':
            if not IDENTITY.fullmatch(decision.get('parentEventId','')) or 'eventId' in decision:
                raise ValueError('A related follow-up must identify its parent without creating an event')
        elif state=='historical_reference':
            posted = date.fromisoformat(candidate['published_at'][:10])
            if posted>=date.fromisoformat(config['observationEarliestDate']):
                raise ValueError('Historical reference is not earlier than registered monitoring')
        elif state!='outside_scope':
            raise ValueError('Unsupported review disposition')
        entries.append(dict(decision=decision,source=candidate,evidencePath=path.relative_to(root).as_posix()))
    now = datetime.now(timezone.utc)
    completed = now if completed_at is None else instant(completed_at)
    if not instant(attempt['readyAt']) <= completed <= now:
        raise ValueError('Review time precedes source archive or is in the future')
    scope = ('candidate_inventory_only' if capture['status']=='archived'
             else 'verified_candidates_from_incomplete_capture')
    return dict(schemaVersion=1,completedAt=completed.isoformat(),attempt=attempt['id'],
                archiveVerifiedAt=attempt['readyAt'],attemptEvidence=attempt['refs'],
                scope=scope,entries=entries)


def verify_review(root, store, folder):
    records = folder/'records'
    verify_bundle(records)
    proof = read(folder/'receipt.json')
    if proof['manifestSha256']!=sha(records/'manifest.json'):
        raise ValueError('Policy review receipt does not match sealed contents')
    expected = read(records/'review.json')
    requested = dict(attempt=expected['attempt'],decisions=[r['decision'] for r in expected['entries']])
    if (expected != build_review(root,store,requested,completed_at=expected['completedAt'])
            or not instant(expected['completedAt'])<=instant(proof['sealedAt'])<=datetime.now(timezone.utc)):
        raise ValueError('Policy review does not reproduce')
    return dict(**expected,sealedAt=proof['sealedAt'],manifestSha256=proof['manifestSha256'])


def reviews_as_of(root,store,ceiling):
    for receipt in sorted((root/'reports/research-policy-reviews').glob('*/receipt.json')):
        if instant(read(receipt)['sealedAt'])<=ceiling:
            yield receipt,verify_review(root,store,receipt.parent)


def seal_review(root, store, requested, folder):
    result = build_review(root,store,requested)
    audit_clock = datetime.now(timezone.utc)
    history = [prior for _,prior in reviews_as_of(root,store,audit_clock)]
    event_ledger([*history,dict(result,sealedAt=audit_clock.isoformat())])
    folder.mkdir(parents=True,exist_ok=False)
    records = folder/'records'
    create(records/'review.json',result)
    seal(records)
    create(folder/'receipt.json',dict(schemaVersion=1,sealedAt=datetime.now(timezone.utc).isoformat(),
                                      manifestSha256=sha(records/'manifest.json')))
    return verify_review(root,store,folder)


def event_ledger(reviews):
    events, dispositions, followups = {},{},{}
    for review in sorted(reviews,key=lambda record: instant(record['sealedAt'])):
        grouped, related = {},[]
        for item in review['entries']:
            decision = item['decision']
            key = decision['revisionKey']
            identity = (decision['disposition'],decision.get('eventId'),decision.get('parentEventId'))
            if dispositions.setdefault(key,identity)!=identity:
                raise ValueError('One source revision received conflicting classifications')
            if decision['disposition']=='event':
                grouped.setdefault(decision['eventId'],[]).append(item)
            elif decision['disposition']=='related_followup':
                related.append(item)
        for key, group in grouped.items():
            head = group[0]['decision']
            event = events.setdefault(key,dict(event_id=key,theme_id=head['themeId'],sources=[],versions=[]))
            if event['theme_id']!=head['themeId']:
                raise ValueError('Policy event theme changed across reviews')
            previous = event['versions'][-1] if event['versions'] else None
            refs = set(previous['source_version_ids']) if previous else set()
            by_url = {source['url']:source['source_version_id'] for source in event['sources']
                      if source['source_version_id'] in refs}
            for item in group:
                c,d = item['source'],item['decision']
                source = dict(event_id=key,url=c['url'],sha256=c['sha256'],captured_at=c['receivedAt'],
                              published_at=c['published_at'],published_at_precision=c['published_at_precision'],
                              timezone=c['timezone'],role=d['role'],evidence=item['evidencePath'])
                last = next((v for v in reversed(event['sources']) if v['url']==c['url']),None)
                if last is None or instant(source['captured_at'])>=instant(last['captured_at']):
                    by_url[c['url']] = append_source_version(event,source)
            next_refs = sorted(set(by_url.values()))
            if not previous or previous['source_version_ids']!=next_refs:
                completion = review['sealedAt']
                event['versions'].append(dict(revision=len(event['versions'])+1,signal_eligible=True,
                    source_version_ids=next_refs,
                    received_at=max((item['source']['receivedAt'] for item in group),key=instant),
                    feature_ready_at=completion,dependency_ready_at=[review['archiveVerifiedAt']],
                    fields=dict(stage=head['stage'])))
        for item in related:
            decision,source = item['decision'],item['source']
            parent = decision['parentEventId']
            if parent not in events:
                raise ValueError('Follow-up parent is missing at the review cutoff')
            followups.setdefault(decision['revisionKey'],dict(parentEventId=parent,url=source['url'],
                    publishedAt=source['published_at'],sha256=source['sha256'],reviewedAt=review['sealedAt'],
                    evidencePath=item['evidencePath']))
    return dict(events=list(events.values()),followups=list(followups.values()))


def policy_ids(ledger, cutoff):
    return {e['event_id'] for e in select_as_of(ledger,cutoff.isoformat())}


def summarize_reviews(reviews,observed):
    ledger = event_ledger(reviews)
    dispositions = {row['decision']['revisionKey']:row['decision']['disposition']
                    for review in reviews for row in review['entries']}
    return dict(schemaVersion=1,asOf=observed.isoformat(),reviewedRevisions=len(dispositions),
                independentEventIds=sorted(policy_ids(ledger,observed)),followups=ledger['followups'],
                lastReviewAt=max((review['sealedAt'] for review in reviews),key=instant,default=None))


def review_progress(root,store,observed):
    reviews = [review for _,review in reviews_as_of(root,store,observed)]
    return summarize_reviews(reviews,observed)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--decisions',type=Path)
    action.add_argument('--verify',type=Path)
    parser.add_argument('--observation-root',type=Path,required=True)
    parser.add_argument('--archive-store',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    root,store=args.observation_root.resolve(),args.archive_store.resolve()
    if args.verify:
        result=verify_review(root,store,args.verify)
    else:
        if args.output is None:
            parser.error('--decisions requires a new --output directory')
        result=seal_review(root,store,read(args.decisions),args.output)
    clock = instant(result['sealedAt'])
    related = any(item['decision']['disposition']=='related_followup' for item in result['entries'])
    history = [prior for _,prior in reviews_as_of(root,store,clock)
               if prior != result] if related else []
    eligible=policy_ids(event_ledger([*history,result]),clock)
    print('PASS',len(result['entries']),'reviewed documents;',len(eligible),'independent events; candidate inventory only')
