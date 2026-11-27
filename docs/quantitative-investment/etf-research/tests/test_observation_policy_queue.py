from datetime import datetime
from hashlib import sha256
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from etf_research.publication import read
from observation_policy_queue import policy_inventory, queue
from pack_observation_evidence import restore_ledger

PACK=ROOT/'reports/2026-11-27-portable-observation/pack'
LATEST='reports/research-observation/runs/2026-11-27/20261127T115450Z-c4c154d1'
EARLY='reports/research-observation/runs/2026-11-27/20261127T112424Z-6c1c8aab'
FOLLOWUP='8c7f46c8042cb2bcef4c8eb556d64d9efe0ab65bdf45b92c54ae8fea14febd3f'


def at(clock):
    return datetime.fromisoformat(f'2026-11-27T{clock}:00+08:00')


class PolicyQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch=TemporaryDirectory()
        cls.addClassCleanup(scratch.cleanup)
        cls.ledger=Path(scratch.name)/'ledger'
        restore_ledger(PACK,cls.ledger)
        cls.store=PACK/'archive'

    def test_same_actual_followup_is_queued_once_then_leaves_after_review(self):
        earlier=queue(self.ledger,self.store,at('19:45'),draft=EARLY)
        self.assertEqual((earlier['completeCaptures'],earlier['observedRevisions'],earlier['reviewedRevisions']),
                         (9,11,10))
        self.assertEqual(len(earlier['pending']),1)
        item=earlier['pending'][0]
        self.assertEqual(item['revisionKey'],FOLLOWUP)
        self.assertEqual(item['appearances'],2)
        self.assertEqual(item['firstSeen']['attempt'],EARLY)
        self.assertEqual(len(earlier['draft']['reusedDecisions']),10)
        self.assertEqual(earlier['draft']['requiresReview'],[item])
        self.assertEqual(earlier['archiveIssues'],[])
        current=queue(self.ledger,self.store,at('21:38'),draft=LATEST)
        self.assertEqual(current['completeCaptures'],10)
        self.assertEqual(current['pending'],[])
        self.assertEqual(len(current['draft']['reusedDecisions']),11)
        self.assertEqual(current['draft']['requiresReview'],[])

    def test_draft_refuses_capture_before_it_was_archived(self):
        with self.assertRaisesRegex(ValueError,'visible at that cutoff'):
            queue(self.ledger,self.store,at('19:45'),draft=LATEST)

    def test_candidate_summary_binding_rejects_changed_manifest(self):
        day='2026-11-27'
        receipt=read(self.ledger/'reports/research-observation/archives'/day/(Path(LATEST).name+'.json'))
        result=read(self.ledger/LATEST/'result.json')
        result['coverage']['evidence']['policyEtf']['manifestSha256']='b'*64
        with self.assertRaisesRegex(ValueError,'manifest reference'):
            policy_inventory(self.store,receipt,result)

    def test_body_revision_stays_queued_when_the_next_capture_reverts(self):
        url='https://www.gov.cn/yaowen/202611/content_100.htm'
        one,two=('a'*64,'b'*64)
        def candidate(digest):
            key=sha256((url+'|'+digest).encode()).hexdigest()
            return dict(revisionKey=key,title='政策变更测试',url=url,sha256=digest,
                        published_at='2026-11-27',receivedAt=at('19:30').isoformat())
        old,changed=candidate(one),candidate(two)
        captures=([old],[changed],[old])
        records=[
            (dict(attempt=f'capture/{i}',archive=str(i)*64,archiveVerifiedAt=at(f'19:4{i}').isoformat(),
                  trigger={'unit':'unit'}),{'index':i}) for i in range(3)
        ]
        review=dict(attempt='capture/0',sealedAt=at('19:50').isoformat(),
                    entries=[dict(decision=dict(revisionKey=old['revisionKey'],disposition='outside_scope'))])
        with (
            patch('observation_policy_queue.archive_index',return_value=({'2026-11-27':records},{})),
            patch('observation_policy_queue.reviews_as_of',return_value=[(None,review)]),
            patch('observation_policy_queue.policy_inventory',
                  side_effect=lambda _,__,record:dict(status='archived',candidates=captures[record['index']])),
        ):
            pending=queue(self.ledger,self.store,at('21:38'))['pending']
        self.assertEqual([row['revisionKey'] for row in pending],[changed['revisionKey']])
        self.assertEqual(pending[0]['previousVersions'],[old['revisionKey']])
        self.assertEqual(pending[0]['firstSeen']['attempt'],'capture/1')


    def test_partial_policy_capture_still_queues_verifiable_articles(self):
        def incomplete_capture(store,receipt,record):
            captured=policy_inventory(store,receipt,record)
            if receipt['attempt']==EARLY:
                return dict(captured,status='coverage_incomplete',issues={'gov_list':'simulated failure'})
            return captured
        with patch('observation_policy_queue.policy_inventory',side_effect=incomplete_capture):
            view=queue(self.ledger,self.store,at('19:45'),draft=EARLY)
        self.assertEqual(view['completeCaptures'],8)
        self.assertEqual(view['observedRevisions'],11)
        self.assertEqual(view['emptyPending'],[])
        self.assertEqual(len(view['incompleteCaptures']),1)
        self.assertEqual(view['incompleteCaptures'][0]['attempt'],EARLY)
        self.assertEqual(view['draft']['captureStatus'],'coverage_incomplete')
        self.assertEqual(view['pending'][0]['revisionKey'],FOLLOWUP)
        self.assertEqual(view['pending'][0]['firstSeen']['captureStatus'],'coverage_incomplete')
        self.assertEqual(view['draft']['requiresReview'],view['pending'])
