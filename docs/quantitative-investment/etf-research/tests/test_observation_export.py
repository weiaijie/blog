from datetime import datetime, timedelta
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from etf_research.publication import atomic, lock, read, sha
from pack_observation_evidence import merge_packs, restore_ledger, verify
from run_observation_export import PUBLISHED, TIMER, chain, register_existing, seal_export

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
            with self.assertRaisesRegex(ValueError,'Published receipt changed'):
                chain(SEED,self.seed_sha,spool)
            (spool/PUBLISHED/(result['latest']['batchId']+'.json')).rename(Path(temporary)/'legacy-receipt.json')
            with self.assertRaisesRegex(ValueError,'Broken export chain'):
                chain(SEED,self.seed_sha,spool)
            with self.assertRaisesRegex(ValueError,'Pinned seed'):
                chain(SEED,'0'*64,spool)

    def test_older_content_damage_blocks_export_until_exact_recovery(self):
        with TemporaryDirectory() as temporary:
            spool=Path(temporary)/'export'
            first=self.publish(spool)
            next_trigger=dict(TRIGGER,invocationId='f'*32)
            second_cutoff=CUTOFF+timedelta(seconds=2)
            second=seal_export(self.ledger,self.store,SEED,self.seed_sha,spool,second_cutoff,next_trigger)
            self.assertEqual(second['verifiedBatchCount'],2)
            self.assertEqual(chain(SEED,self.seed_sha,spool)['verifiedBatchCount'],1)
            self.assertEqual(chain(SEED,self.seed_sha,spool,full=True)['verifiedBatchCount'],2)

            old_pack=spool/'batches'/first['latest']['batchId']/'pack'
            obj=next((old_pack/'archive/objects').glob('*/*'))
            reference=DELTA/obj.relative_to(old_pack)
            self.assertEqual(sha(reference),sha(obj))
            obj.write_bytes(b'corrupt older content')
            fast=chain(SEED,self.seed_sha,spool)
            self.assertEqual(fast['manifestSha256'],second['manifestSha256'])
            with self.assertRaisesRegex(ValueError,first['latest']['batchId']):
                chain(SEED,self.seed_sha,spool,full=True)

            third_cutoff=CUTOFF+timedelta(seconds=4)
            third_trigger=dict(TRIGGER,invocationId='a'*32)
            with self.assertRaisesRegex(ValueError,first['latest']['batchId']):
                seal_export(self.ledger,self.store,SEED,self.seed_sha,spool,third_cutoff,third_trigger)
            self.assertEqual(chain(SEED,self.seed_sha,spool),fast)
            [failure]=(spool/'audit-failures').glob('*.json')
            self.assertIn(first['latest']['batchId'],read(failure)['error'])
            self.assertEqual(read(failure)['trigger'],third_trigger)

            obj.write_bytes(reference.read_bytes())
            repaired=seal_export(self.ledger,self.store,SEED,self.seed_sha,spool,third_cutoff,third_trigger)
            self.assertEqual(repaired['verifiedBatchCount'],3)
            self.assertEqual(repaired['latest']['after'],second['through'])
            self.assertTrue(failure.is_file())

    def test_published_suffix_cannot_disappear_or_start_over(self):
        with TemporaryDirectory() as temporary:
            base=Path(temporary)
            spool=base/'export'
            first=self.publish(spool)
            later=CUTOFF+timedelta(seconds=2)
            trigger=dict(TRIGGER,invocationId='1'*32)
            second=seal_export(self.ledger,self.store,SEED,self.seed_sha,spool,later,trigger)
            self.assertEqual(second['registeredBatchCount'],2)
            tail=second['latest']['batchId']
            path=spool/'batches'/tail
            pinned=spool/PUBLISHED/(tail+'.json')
            self.assertEqual(sha(pinned),sha(path/'receipt.json'))

            # Existing valid exports can be registered again after an interrupted backfill.
            elsewhere=base/pinned.name
            pinned.rename(elsewhere)
            legacy=chain(SEED,self.seed_sha,spool,full=True)
            self.assertEqual(legacy['registeredBatchCount'],1)
            with lock(spool/'export.lock'):
                self.assertEqual(register_existing(spool,legacy)['registeredBatchCount'],2)
            self.assertEqual(sha(pinned),sha(elsewhere))

            relocated=base/'restored-from-backup'
            path.rename(relocated)
            with self.assertRaisesRegex(ValueError,'Published export batch is missing: '+tail):
                chain(SEED,self.seed_sha,spool)
            retry=later+timedelta(seconds=2)
            third=dict(TRIGGER,invocationId='2'*32)
            with self.assertRaisesRegex(ValueError,'Published export batch is missing: '+tail):
                seal_export(self.ledger,self.store,SEED,self.seed_sha,spool,retry,third)
            self.assertEqual([p.name for p in (spool/'batches').iterdir()],[first['latest']['batchId']])
            self.assertIn(tail,read(next((spool/'audit-failures').glob('*.json')))['error'])

            relocated.rename(path)
            result=seal_export(self.ledger,self.store,SEED,self.seed_sha,spool,retry,third)
            self.assertEqual(result['latest']['after'],second['through'])
            self.assertEqual(result['registeredBatchCount'],3)
