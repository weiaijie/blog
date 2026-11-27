"""Build the registered policy input only from reviewed, as-of coverage."""
from datetime import datetime, timedelta
from observation_archive import open_attempt
from review_policy_observations import event_ledger, policy_ids, reviews_as_of
from etf_research.observation_experiment import DECISION_TIME
from etf_research.observation_slots import POLL_TIMES, scheduled_slot
from etf_research.policy_events import TZ, instant
from etf_research.publication import read, sha

def expected_slots(start, end):
    current = start.astimezone(TZ).date()
    last = end.astimezone(TZ).date()
    slots = []
    while current<=last:
        for clock in POLL_TIMES:
            slot = datetime.combine(current,clock,TZ)
            if start<slot<=end:
                slots.append(slot)
        current += timedelta(days=1)
    return slots


def assess(cutoffs, polls, reviews, ceiling):
    """Distinguish reviewed observed events from a complete five-interval feature."""
    if len(cutoffs)!=6 or list(cutoffs)!=sorted(set(cutoffs)):
        raise ValueError('Six ordered decision cutoffs are required')
    valid_reviews = [row for row in reviews if instant(row['sealedAt'])<=ceiling]
    ledger = event_ledger(valid_reviews)
    review_times, reviewed_attempts = {}, {}
    for row in sorted(valid_reviews,key=lambda item:instant(item['sealedAt'])):
        reviewed_attempts.setdefault(row['attempt'],row['sealedAt'])
        for candidate in row['entries']:
            review_times.setdefault(candidate['decision']['revisionKey'], row['sealedAt'])
    by_slot = {}
    for poll in polls:
        slot = scheduled_slot(poll)
        if slot is not None and cutoffs[0]<slot<=cutoffs[-1]:
            by_slot.setdefault(slot,[]).append(poll)

    intervals, dependencies, proofs = [], [], []
    for start, end in zip(cutoffs,cutoffs[1:]):
        until = min(end,ceiling)
        missing, pending, upcoming = [], [], []
        for slot in expected_slots(start,end):
            if slot>until:
                upcoming.append(slot.isoformat())
                continue
            eligible = [row for row in by_slot.get(slot,[]) if instant(row['readyAt'])<=until]
            if not any(row['policyEtf']['policy']['status']=='archived' for row in eligible):
                missing.append(slot.isoformat())
                continue
            keys = {c['revisionKey'] for row in eligible for c in row['policyEtf']['policy']['candidates']}
            unknown = sorted(key for key in keys if key not in review_times or instant(review_times[key])>until)
            empty_unchecked = not keys and not any(
                row['id'] in reviewed_attempts and instant(reviewed_attempts[row['id']])<=until
                for row in eligible if row['policyEtf']['policy']['status']=='archived')
            if unknown or empty_unchecked:
                pending.append(dict(slot=slot.isoformat(),unreviewedRevisions=unknown,
                                    emptyCaptureUnchecked=empty_unchecked))
            else:
                dependencies.extend(row['readyAt'] for row in eligible)
                dependencies.extend(review_times[key] for key in keys)
                dependencies.extend(reviewed_attempts[row['id']] for row in eligible
                                    if not keys and row['id'] in reviewed_attempts
                                    and instant(reviewed_attempts[row['id']])<=until)
                proofs.extend(ref for row in eligible for ref in row['refs'])
        intervals.append(dict(startAt=start.isoformat(),endAt=end.isoformat(),sourceScope='gov-list-csrc-home',
                              complete=not (missing or pending or upcoming),missingPolls=missing,
                              upcomingPolls=upcoming,pendingReviews=pending))
    complete = sum(row['complete'] for row in intervals)
    events = sorted(policy_ids(ledger,min(cutoffs[-1],ceiling))-policy_ids(ledger,cutoffs[0]))
    known = dict(coveredIntervals=complete,expectedIntervals=5,intervals=intervals,
                 observedReviewedEventIds=events)
    if ledger['followups']:
        known['relatedFollowups'] = ledger['followups']
    if complete==5:
        known.update(count=len(events),eventIds=events,dependencyReadyAt=dependencies,pollEvidence=proofs)
    else:
        known.update(count=None,eventIds=[])
    return known


def load_policy_context(root, store, dates, entry, ceiling):
    reviews, proofs = [], []
    for receipt,review in reviews_as_of(root,store,ceiling):
        reviews.append(review)
        proofs.extend([dict(root='observations',path=receipt.relative_to(root).as_posix(),sha256=sha(receipt)),
                       *review['attemptEvidence']])
    if not reviews:
        return None
    days = (*dates[-5:],entry)
    cutoffs = tuple(datetime.combine(day,DECISION_TIME,TZ) for day in days)
    polls = []
    config = read(root/'config/research_observation.json')
    # A successful policy poll may belong to a catch-up attempt for an older session.
    for proof in (root/'reports/research-observation/archives').glob('*/*.json'):
        ready = instant(read(proof)['archiveVerifiedAt'])
        if not cutoffs[0]<ready<=ceiling:
            continue
        folder = root/'reports/research-observation/runs'/proof.parent.name/proof.stem
        record = read(folder/'result.json')
        started = instant(record['startedAt'])
        if cutoffs[0]<started<=ceiling and scheduled_slot(record) is not None:
            attempt = open_attempt(root,store,folder,config)
            if attempt is not None:
                polls.append(attempt)
    status = assess(cutoffs,polls,reviews,ceiling)
    status['reviewEvidence'] = proofs
    status['reviewReadyAt'] = max((r['sealedAt'] for r in reviews),key=instant)
    return status
