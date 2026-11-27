from datetime import datetime, timedelta
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from etf_research.publication import atomic, read, sha
from pack_observation_evidence import merge_packs, restore_ledger, verify
from run_observation_export import TIMER, chain, seal_export

SEED=ROOT/'reports/2026-11-27-portable-observation/pack'
DELTA=ROOT/'reports/2026-11-27-after-filing/pack'
CUTOFF=datetime.fromisoformat('2026-11-27T22:07:00+08:00')
TRIGGER=dict(unit=TIMER,invocationId='e'*32,timerRealtimeUsec=None)


class ObservationExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary=TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        base=Path(temporary.name)
        merged=base/'merged'
        merge_packs([SEED,DELTA],merged)
        cls.ledger=base/'ledger'
        restore_ledger(merged,cls.ledger)
        cls.store=merged/'archive'
        cls.seed_sha=sha(SEED/'manifest.json')

    def publish(self,spool,cutoff=CUTOFF):
        return seal_export(self.ledger,self.store,SEED,self.seed_sha,spool,cutoff,TRIGGER)

    def test_single_batch_is_verified_and_same_invocation_cannot_append(self):
        with TemporaryDirectory() as temporary:
            spool=Path(temporary)/'export'
            result=self.publish(spool)
            self.assertEqual(result['status'],'sealed')
            self.assertEqual(result['batchCount'],1)
            self.assertEqual(result['latest']['receipts'],{'observation':1})
            pack=spool/'batches'/result['latest']['batchId']/'pack'
            self.assertEqual(verify(pack)['after'],result['seedAsOf'])
            self.assertEqual(self.publish(spool,CUTOFF+timedelta(seconds=1))['status'],'already_sealed')
            self.assertEqual(chain(SEED,self.seed_sha,spool)['batchCount'],1)
            following=seal_export(self.ledger,self.store,SEED,self.seed_sha,spool,
                                  CUTOFF+timedelta(seconds=2),dict(TRIGGER,invocationId='f'*32))
            self.assertEqual(following['batchCount'],2)
            self.assertEqual(following['latest']['receipts'],{})
            self.assertEqual(following['latest']['after'],result['through'])

    def test_failure_preserves_staging_and_retries_same_boundary(self):
        with TemporaryDirectory() as temporary:
            spool=Path(temporary)/'export'
            with patch('run_observation_export.export',side_effect=OSError('test interrupted')):
                with self.assertRaisesRegex(OSError,'test interrupted'):
                    self.publish(spool)
            failed=chain(SEED,self.seed_sha,spool)
            self.assertEqual(failed['batchCount'],0)
            self.assertEqual(failed['stagedAttempts'],1)
            actual=self.publish(spool)
            self.assertEqual(actual['latest']['after'],failed['through'])
            self.assertEqual(actual['latest']['receipts'],{'observation':1})

    def test_corrupt_link_blocks_future_export(self):
        with TemporaryDirectory() as temporary:
            spool=Path(temporary)/'export'
            result=self.publish(spool)
            path=spool/'batches'/result['latest']['batchId']/'receipt.json'
            payload=read(path)
            atomic(path,dict(payload,previousManifestSha256='0'*64))
            with self.assertRaisesRegex(ValueError,'Broken export chain'):
                chain(SEED,self.seed_sha,spool)
            with self.assertRaisesRegex(ValueError,'Pinned seed'):
                chain(SEED,'0'*64,spool)
