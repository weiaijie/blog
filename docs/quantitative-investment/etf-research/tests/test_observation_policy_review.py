from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest

from etf_research.policy_events import TZ, instant
from etf_research.publication import read

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))

from observation_policy_inputs import assess, expected_slots, scheduled_slot
from review_policy_observations import build_review, event_ledger, policy_ids, verify_review
from observation_inputs import assemble

REPORT = ROOT/'reports/2026-11-27-policy-review'
REVIEW = ROOT/'reports/research-policy-reviews/2026-11-27-capture-092054'
STORE = ROOT/'reports/2026-11-27-observation-inputs/archive-proofs'
EVENT = 'state-council-2026-11-27-stabilization'


class ObservationPolicyReviewTests(unittest.TestCase):
    def test_real_candidates_group_into_one_new_event_at_seal_time(self):
        review = verify_review(ROOT, STORE, REVIEW)
        self.assertEqual(Counter(row['decision']['disposition'] for row in review['entries']),
                         dict(event=2, historical_reference=7, outside_scope=1))
        ledger = event_ledger([review])
        self.assertEqual(len(ledger['events'][0]['sources']), 2)
        sealed = instant(review['sealedAt'])
        self.assertEqual(policy_ids(ledger, sealed-timedelta(microseconds=1)), set())
        self.assertEqual(policy_ids(ledger, sealed), {EVENT})

    def test_linked_later_disclosure_keeps_parent_event_count_and_first_ready_clock(self):
        review = verify_review(ROOT, STORE, REVIEW)
        follow_clock = instant(review['sealedAt'])+timedelta(minutes=10)
        key = 'a'*64
        child = dict(decision=dict(disposition='related_followup',revisionKey=key,parentEventId=EVENT),
                     source=dict(url='https://www.csrc.gov.cn/public-note',sha256='b'*64,
                                 published_at=follow_clock.isoformat()),evidencePath='archived-source.body')
        update = dict(archiveVerifiedAt=follow_clock.isoformat(),sealedAt=follow_clock.isoformat(),entries=[child])
        ledger = event_ledger([review,update])
        self.assertEqual(policy_ids(ledger,follow_clock),{EVENT})
        self.assertEqual(ledger['events'],event_ledger([review])['events'])
        self.assertEqual(ledger['followups'][0]['parentEventId'],EVENT)
        self.assertEqual(ledger['followups'][0]['reviewedAt'],follow_clock.isoformat())
        with self.assertRaisesRegex(ValueError,'parent is missing'):
            event_ledger([update])
        revised = dict(child,decision=dict(child['decision'],parentEventId='another-parent'))
        with self.assertRaisesRegex(ValueError,'conflicting classifications'):
            event_ledger([review,update,dict(update,entries=[revised])])

    def test_incomplete_or_unbound_decisions_fail(self):
        request = read(REPORT/'decisions.json')
        partial = dict(request, decisions=request['decisions'][1:])
        with self.assertRaisesRegex(ValueError, 'exactly once'):
            build_review(ROOT, STORE, partial)
        request['decisions'][0]['locator'] = 'a string that cannot appear in this archived article'
        with self.assertRaisesRegex(ValueError, 'candidate body'):
            build_review(ROOT, STORE, request)

    def test_production_probe_preserves_unavailable_policy_feature(self):
        saved = read(REPORT/'coverage-probe.json')
        actual = assemble(ROOT, ROOT, STORE, instant(saved['deadline']).date(),
                          instant(saved['observedAt']), computed=instant(saved['computedAt']))
        self.assertEqual(saved, actual)
        self.assertIsNone(actual['cells']['policyActiveCount'])
        scope = actual['gaps']['policyActiveCount']['reviewedScope']
        self.assertEqual(scope['observedReviewedEventIds'], [EVENT])
        self.assertEqual(scope['coveredIntervals'], 0)
        self.assertEqual(sum(len(row['missingPolls']) for row in scope['intervals']), 8)
        self.assertEqual(sum(len(row['upcomingPolls']) for row in scope['intervals']), 6)

    def test_complete_and_timely_empty_scope_yields_zero_only_with_reviews(self):
        cutoffs = [datetime(2026, 11, day, 8, 55, tzinfo=TZ) for day in (23,24,25,26,27,30)]
        slots = expected_slots(cutoffs[0], cutoffs[-1])
        polls, reviews = [], []
        for index, slot in enumerate(slots):
            attempt = str(index)
            started = (slot+timedelta(seconds=1)).isoformat()
            ready = (slot+timedelta(seconds=3)).isoformat()
            trigger = dict(unit='etf-research-observation.timer',
                           timerRealtimeUsec=int(slot.timestamp()*1_000_000))
            polls.append(dict(trigger=trigger, startedAt=started, readyAt=ready, id=attempt,
                              policyEtf=dict(policy=dict(status='archived', candidates=[])), refs=[]))
            reviews.append(dict(attempt=attempt, sealedAt=(slot+timedelta(seconds=5)).isoformat(),
                                entries=[], archiveVerifiedAt=ready))
            self.assertEqual(scheduled_slot(polls[-1]), slot)

        end = cutoffs[-1]
        self.assertEqual(assess(cutoffs, polls, reviews, end)['coveredIntervals'], 5)
        self.assertEqual(assess(cutoffs, polls, reviews, end)['count'], 0)
        self.assertIsNone(assess(cutoffs, polls[1:], reviews, end)['count'])
        self.assertIsNone(assess(cutoffs, polls, reviews[1:], end)['count'])
        late_review = dict(reviews[0], sealedAt=(cutoffs[1]+timedelta(seconds=1)).isoformat())
        self.assertIsNone(assess(cutoffs, polls, [late_review, *reviews[1:]], end)['count'])
        nonscheduled = dict(polls[0], startedAt=(slots[0]+timedelta(minutes=1)).isoformat())
        self.assertIsNone(assess(cutoffs, [nonscheduled, *polls[1:]], reviews, end)['count'])
