from copy import deepcopy
from pathlib import Path
import unittest

from etf_research.policy_events import append_source_version, build_pilot, select_as_of

ROOT = Path(__file__).resolve().parents[1]


class PolicyEventTests(unittest.TestCase):
    def setUp(self):
        self.event = dict(event_id='meeting-1', theme_id='stability', sources=[], versions=[])
        self.source = dict(event_id='meeting-1', url='https://www.news.cn/example',
            sha256='a'*64, captured_at='2026-11-27T12:40:00+08:00',
            published_at='2026-11-27T12:24:37+08:00', published_at_precision='second',
            timezone='Asia/Shanghai')
        self.ref = append_source_version(self.event, self.source)
        self.v = dict(revision=1, source_version_ids=[self.ref], received_at='2026-11-27T12:40:00+08:00',
                    feature_ready_at='2026-11-27T13:00:00+08:00', dependency_ready_at=[],
                    signal_eligible=True, fields={'stage':'deployment'})
        self.event['versions'].append(self.v)
        self.ledger = dict(events=[self.event])

    def test_clock_gates_and_equivalent_instants(self):
        self.assertEqual(select_as_of(self.ledger,'2026-11-27T12:30:00+08:00'), [])
        self.assertEqual(select_as_of(self.ledger,'2026-11-27T12:59:59+08:00'), [])
        self.assertEqual(select_as_of(self.ledger,'2026-11-27T05:00:00Z')[0]['revision'],1)
        self.v['dependency_ready_at'] = ['2026-11-27T16:00:00+08:00']
        self.assertEqual(select_as_of(self.ledger,'2026-11-27T15:00:00+08:00'), [])
        self.assertEqual(len(select_as_of(self.ledger,'2026-11-27T16:00:00+08:00')),1)

    def test_reject_unknown_and_timezone_conflicts(self):
        for invalid in ('2026-11-27T13:01:00', '2026-11-27T13:01:00+08:99'):
            with self.subTest(decision=invalid), self.assertRaises(ValueError):
                select_as_of(self.ledger, invalid)
        with self.assertRaises(ValueError):
            append_source_version(self.event, dict(self.source, published_at='2026-11-27T12:24:37-05:00'))
        for key, value in [('received_at',None), ('feature_ready_at',None), ('dependency_ready_at',[None])]:
            with self.subTest(key=key):
                clone = deepcopy(self.ledger)
                clone['events'][0]['versions'][0][key] = value
                self.assertEqual(select_as_of(clone,'2026-12-01T00:00:00Z'), [])

    def test_known_date_cannot_supply_an_intraday_publication_time(self):
        self.event['sources'][0].update(published_at='2026-11-27', published_at_precision='date')
        self.assertEqual(select_as_of(self.ledger,'2026-11-27T23:59:59+08:00'), [])
        self.assertEqual(len(select_as_of(self.ledger,'2026-11-28T00:00:00+08:00')),1)

    def test_repeat_capture_and_later_correction(self):
        later = '2026-11-28T09:30:00+08:00'
        self.assertEqual(append_source_version(self.event,dict(self.source,captured_at=later)),self.ref)
        ref2 = append_source_version(self.event,dict(self.source,captured_at=later,sha256='b'*64))
        self.assertNotEqual(self.ref, ref2)
        self.event['versions'].append(dict(self.v, revision=2, source_version_ids=[ref2],
            received_at=later, feature_ready_at='2026-11-28T10:00:00+08:00', fields={'stage':'adjustment'}))
        old = select_as_of(self.ledger,'2026-11-27T16:00:00+08:00')[0]
        self.assertEqual((old['fields']['stage'], old['sources'][0]['sha256']),('deployment','a'*64))
        new = select_as_of(self.ledger,'2026-11-28T10:00:00+08:00')[0]
        self.assertEqual((new['fields']['stage'], new['sources'][0]['sha256']),('adjustment','b'*64))
        with self.assertRaises(ValueError):
            append_source_version(self.event,dict(self.source,captured_at=later,sha256='c'*64))

    def test_deduplication_and_immutable_pilot(self):
        ledger = build_pilot(ROOT)
        self.assertEqual(len(ledger['events']), 2)
        self.assertEqual(len({e['event_id'] for e in ledger['events']}),2)
        self.assertEqual(len({e['theme_id'] for e in ledger['events']}),1)
        for e in ledger['events']:
            self.assertEqual(len(e['versions']),1)
            self.assertEqual([s['role'] for s in e['sources']],['original','government_reprint'])
            self.assertIsNone(e['received_at'])
        for decision in ('2026-11-06T20:00:00+08:00','2026-11-27T12:45:00+08:00','2027-01-01T00:00:00Z'):
            self.assertEqual(select_as_of(ledger,decision),[])
