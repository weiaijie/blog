from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.policy_events import instant
from etf_research.exchange_calendar import BASE_PATH

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from observation_evaluation_status import evaluation_view
import seal_observation_evaluation as publisher

ORIGIN=dict(date='2026-11-27',archiveVerifiedAt='2026-11-27T18:42:03+08:00')


class EvaluationStatusTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        base=Path(directory.name)
        self.root,self.store=base/'observation',base/'archive'
        self.root.mkdir()
        calendar=self.root/BASE_PATH
        calendar.parent.mkdir(parents=True)
        calendar.write_bytes((ROOT/BASE_PATH).read_bytes())

    def publish(self, stamp, invocation, *, started):
        scored=dict(score=dict(status='observation_in_progress',completedPairs=34,quarters=1,independentEvents=4),
                    shortfall=dict(pairs=86,folds=1,policyEvents=16),foldCoverage={},
                    economics=dict(selectedWindows=10,matchedWindows=7,gaps={}),coverage=[])
        report=dict(schemaVersion=1,asOf=stamp,status='observation_in_progress' if started else 'observation_origin_pending',
                    studyOrigin=ORIGIN if started else None,thresholds=dict(pairs=120,folds=2,policyEvents=20),
                    comparisons={'combined':scored} if started else {},folds=[])
        clock=instant(stamp)
        with (patch.object(publisher,'now',return_value=clock),patch.object(publisher,'CODE',()),
              patch('etf_research.evidence_archive.datetime') as archived):
            archived.now.return_value=clock
            receipt=publisher.archive_evaluation(self.root,self.store,report,invocation)
        return receipt,report

    def test_missing_archive_never_claims_measured_progress(self):
        observed=instant('2026-11-27T19:00:00+08:00')
        no_origin=evaluation_view(self.root,self.store,observed,None,details=True)
        self.assertEqual(no_origin['archiveState'],'waiting')
        self.assertIsNone(no_origin['report'])
        self.assertIsNone(no_origin['assessedAt'])
        self.assertEqual(no_origin['comparisons']['combined']['completedPairs'],0)
        self.assertEqual(no_origin['comparisons']['combined']['shortfall']['policyEvents'],20)
        self.assertIsNone(no_origin['comparisons']['etf']['policyEvents'])
        after_origin=evaluation_view(self.root,self.store,observed,ORIGIN)
        self.assertEqual(after_origin['status'],'awaiting_evaluation')
        self.assertIsNone(after_origin['comparisons']['combined']['completedPairs'])

    def test_pinned_archive_identical_to_summary_and_immutable_after_corruption(self):
        early='2026-11-26T20:45:00+08:00'
        newer='2026-11-27T20:45:00+08:00'
        a,first=self.publish(early,'a'*32,started=False)
        b,second=self.publish(newer,'b'*32,started=True)
        before=instant('2026-11-27T20:44:00+08:00')
        old=evaluation_view(self.root,self.store,before,ORIGIN,details=True)
        self.assertEqual(old['report'],first)
        self.assertEqual(old['archiveSha256'],a['archiveSha256'])
        self.assertTrue(old['originSinceArchive'])
        after=instant('2026-11-28T08:00:00+08:00')
        latest=evaluation_view(self.root,self.store,after,ORIGIN)
        pinned=evaluation_view(self.root,self.store,after,ORIGIN,archive=b['archiveSha256'],details=True)
        self.assertEqual(pinned['report'],second)
        self.assertEqual(latest['comparisons'],pinned['comparisons'])
        self.assertEqual(pinned['comparisons']['combined']['shortfall'],dict(pairs=86,folds=1,policyEvents=16))
        self.assertNotIn('report',latest)
        (self.root/b['path']/'records/evaluation.json').write_bytes(b'{}')
        fallback=evaluation_view(self.root,self.store,after,ORIGIN,details=True)
        self.assertEqual(fallback['archiveSha256'],a['archiveSha256'])
        self.assertEqual(fallback['archiveIssues']['unverified'],1)
        rejected=evaluation_view(self.root,self.store,after,ORIGIN,archive=b['archiveSha256'],details=True)
        self.assertEqual(rejected['archiveState'],'unverified')
        self.assertIsNone(rejected['report'])
