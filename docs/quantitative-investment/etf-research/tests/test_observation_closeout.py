from copy import deepcopy
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

import build_observation_closeout as closeout
from etf_research.publication import create, read, sha

ORIGIN = dict(date='2025-10-09',archiveVerifiedAt='2025-10-09T19:40:03+08:00')
STAMP = '2026-10-10T20:45:00+08:00'
PUBLIC = dict(publishedThrough='2026-10-10T22:20:00+08:00',publishedManifestSha256='1'*64)
RECEIPT = dict(path='reports/research-evaluation/2026-10-10/'+'a'*32,archiveSha256='2'*64)


class StudyCloseoutTests(unittest.TestCase):
    def sample(self):
        group = dict(score=dict(status='insufficient_samples',completedPairs=24,quarters=1,independentEvents=0),
                     shortfall=dict(pairs=96,folds=1,policyEvents=20),
                     economics=dict(selectedWindows=38,matchedWindows=9,gaps={}),coverage=[])
        return dict(status='evaluation_available',studyOrigin=ORIGIN,finalOn='2026-10-09',asOf=STAMP,
                    comparisons={key:deepcopy(group) for key in closeout.VARIANT_NAMES})

    def test_no_origin_or_unverified_evaluation_cannot_be_exported_as_result(self):
        with patch.object(closeout,'first_archive',return_value=None):
            self.assertEqual(closeout.from_evidence(ROOT,ROOT,ROOT,PUBLIC)['status'],'observation_origin_pending')
        with (
            patch.object(closeout,'first_archive',return_value=ORIGIN),
            patch.object(closeout,'latest_evaluation',return_value=((RECEIPT,self.sample()),dict(unverified=1,pending=0))),
        ):
            self.assertEqual(closeout.from_evidence(ROOT,ROOT,ROOT,PUBLIC)['status'],'evaluation_evidence_unverified')

    def test_held_labels_and_economic_evidence_have_separate_states(self):
        sample = self.sample()
        receipt_view = ((RECEIPT,sample),dict(unverified=0,pending=0))
        with patch.object(closeout,'first_archive',return_value=ORIGIN),patch.object(closeout,'latest_evaluation',return_value=receipt_view):
            sample['status']='final_labels_pending'
            self.assertEqual(closeout.from_evidence(ROOT,ROOT,ROOT,PUBLIC)['status'],'final_labels_pending')
            sample['status']='evaluation_available'
            sample['comparisons']['combined']['economics']['status']='economic_evidence_unverified'
            self.assertEqual(closeout.from_evidence(ROOT,ROOT,ROOT,PUBLIC)['status'],'economic_evidence_unverified')

    def test_cutoff_replay_and_protocol_pin_are_required_before_reporting_sample_shortfall(self):
        sample=self.sample()
        with TemporaryDirectory() as directory:
            root=Path(directory)
            packet=root/RECEIPT['path']/'records/evaluation.json'
            create(packet,dict(codeSha256={'PROTOCOL_OBSERVATION_V1.md':sha(ROOT/'PROTOCOL_OBSERVATION_V1.md')}))
            with (
                patch.object(closeout,'first_archive',return_value=ORIGIN),
                patch.object(closeout,'latest_evaluation',return_value=((RECEIPT,sample),dict(unverified=0,pending=0))) as locate,
                patch.object(closeout,'evaluate',return_value=sample) as replay,
                patch.object(closeout,'publication_report',return_value=None),
            ):
                result=closeout.from_evidence(ROOT,root,root,PUBLIC,archive=RECEIPT['archiveSha256'])
                report=closeout.render(result)
                self.assertIn('样本不足',report)
                self.assertIn('还差 96 个日期',report)
                self.assertIn('账户发布证据待核验',report)
                self.assertEqual(locate.call_args.kwargs['archive'],RECEIPT['archiveSha256'])
                self.assertEqual(replay.call_args.args[2].isoformat(),STAMP)
                replay.return_value=dict(sample,finalOn='2026-10-10')
                with self.assertRaisesRegex(ValueError,'does not reproduce'):
                    closeout.from_evidence(ROOT,root,root,PUBLIC)
                packet.write_text('{"codeSha256":{"PROTOCOL_OBSERVATION_V1.md":"different"}}',encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'protocol differs'):
                    closeout.from_evidence(ROOT,root,root,PUBLIC)

    def test_output_is_only_created_when_evidence_is_ready(self):
        with TemporaryDirectory() as directory:
            output=Path(directory)/'report'
            ready=dict(status='ready',publishedThrough=STAMP,evaluation=self.sample(),evaluationReceipt=RECEIPT,
                       publishedManifestSha256=PUBLIC['publishedManifestSha256'],forward=None)
            with patch.object(closeout,'audit'),patch.object(closeout,'from_evidence',return_value=dict(status='final_labels_pending')):
                self.assertEqual(closeout.run(ROOT,output)['status'],'final_labels_pending')
            self.assertFalse(output.exists())
            with patch.object(closeout,'audit'),patch.object(closeout,'from_evidence',return_value=ready):
                self.assertEqual(closeout.run(ROOT,output)['status'],'ready')
            self.assertEqual(read(output/'result.json'),ready)
            self.assertIn(RECEIPT['archiveSha256'],(output/'README.md').read_text(encoding='utf-8'))
