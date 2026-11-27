from datetime import datetime
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from etf_research.publication import read
from observation_status import report
from observation_out_of_sample import evaluate
from review_policy_observations import review_progress
from pack_observation_evidence import export, restore_ledger, restore_receipt, verify
from seal_observation_evaluation import verify_evaluation

PACK=ROOT/'reports/2026-11-27-portable-observation/pack'
CUTOFF=datetime.fromisoformat('2026-11-27T21:10:38+08:00')
EVAL='reports/research-evaluation/2026-11-27/50942c432a3e424ba41cc7719cb95583/receipt.json'


class PortableObservationTests(unittest.TestCase):
    def test_offline_ledger_and_evaluation_replay(self):
        expected=verify(PACK)
        self.assertEqual(expected['receipts'],{'observation':10,'policy_review':2,'evaluation':1})
        self.assertEqual(expected['archives'],11)
        with tempfile.TemporaryDirectory() as temporary:
            ledger=Path(temporary)/'new-ledger'
            summary=restore_ledger(PACK,ledger)
            self.assertFalse(summary['activates_services'])
            view=report(ledger,PACK/'archive',observed=CUTOFF)
            self.assertEqual(view['counts'],dict(expected=1,archived=1,qualified=0,missing=0))
            self.assertIsNone(view['firstQualifiedArchive'])
            self.assertEqual(view['evaluation']['status'],'observation_origin_pending')
            zoom=report(ledger,PACK/'archive',day='2026-11-27',observed=CUTOFF)['session']
            self.assertEqual(zoom['latestSourceEvidence']['archiveSha256'],zoom['latest']['archiveSha256'])
            self.assertEqual(len(zoom['latestSourceEvidence']['requests']),6)
            self.assertFalse((ledger/'config/active_run.json').exists())
            restored=Path(temporary)/'evaluation'
            proof=restore_receipt(PACK,EVAL,restored)
            self.assertEqual(proof['verified_files'],20)
            receipt,packet=verify_evaluation(restored,PACK/'archive',(restored/EVAL).parent,observed=CUTOFF)
            self.assertEqual(receipt['archiveSha256'],proof['snapshot'])
            self.assertEqual(packet['status'],'observation_origin_pending')
            self.assertEqual(evaluate(ledger,PACK/'archive',datetime.fromisoformat(packet['asOf'])),packet)
            reviews=review_progress(ledger,PACK/'archive',CUTOFF)
            self.assertEqual(reviews['reviewedRevisions'],11)
            self.assertEqual(len(reviews['independentEventIds']),1)

    def test_incremental_export_respects_receipt_cutoffs(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger=Path(temporary)/'ledger'
            pack=Path(temporary)/'incremental'
            restore_ledger(PACK,ledger)
            summary=export(ledger,PACK/'archive',pack,CUTOFF,
                           after=datetime.fromisoformat('2026-11-27T20:44:00+08:00'))
            self.assertEqual(summary['receipts'],{'evaluation':1})
            index=read(pack/'index.json')
            self.assertEqual([row['receipt'] for row in index['receipts']],[EVAL])
            self.assertEqual(verify(pack),summary)

    def test_restore_refuses_unsealed_bytes_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with self.assertRaises(FileExistsError):
                restore_ledger(PACK,root)
            pack=shutil.copytree(PACK,root/'changed')
            obj=next((pack/'archive/objects').glob('*/*'))
            obj.write_bytes(b'invalid evidence')
            with self.assertRaises(ValueError):
                restore_ledger(pack,root/'destination')
            self.assertFalse((root/'destination').exists())
