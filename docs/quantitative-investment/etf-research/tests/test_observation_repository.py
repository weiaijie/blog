from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from shutil import copytree
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from audit_observation_repository import CATALOG, audit
from etf_research.policy_events import instant
from etf_research.publication import create, read, sha
from run_observation_export import TIMER, seal_export


def first_published_batch():
    catalog = read(ROOT/CATALOG)
    catalog['batches'] = catalog['batches'][:1]
    row = catalog['batches'][0]
    receipt = read(ROOT/row['receipt'])
    catalog['head'] = dict(batchId=row['batchId'],manifestSha256=receipt['packManifestSha256'])
    return catalog


class ObservationRepositoryTests(unittest.TestCase):
    def test_public_exports_match_live_prefix_and_restore_original_evidence(self):
        catalog = first_published_batch()
        row = catalog['batches'][0]
        with TemporaryDirectory() as temp:
            base = Path(temp)
            recovery = base/'recovery'
            result = audit(ROOT,catalog,destination=recovery)
            self.assertEqual(result['publishedBatchCount'],1)
            self.assertEqual(result['restored']['receipts'],
                             {'observation':11,'policy_review':2,'evaluation':1})
            self.assertFalse(result['restored']['activates_services'])
            receipt = read(ROOT/row['receipt'])
            spool = base/'spool'
            batch = spool/'batches'/row['batchId']
            copytree(ROOT/row['pack'],batch/'pack')
            (batch/'receipt.json').write_bytes((ROOT/row['receipt']).read_bytes())
            create(batch/'started.json',{key:receipt[key] for key in ('asOf','after','trigger')})
            view = audit(ROOT,catalog,live_spool=spool)['liveComparison']
            self.assertEqual(view['unpublishedBatchIds'],[])
            next_export = seal_export(recovery/'ledger',recovery/'pack/archive',ROOT/catalog['seed']['pack'],
                                      catalog['seed']['manifestSha256'],spool,instant(receipt['asOf'])+timedelta(seconds=2),
                                      dict(unit=TIMER,invocationId='f'*32,timerRealtimeUsec=None))
            result = audit(ROOT,catalog,live_spool=spool)
            self.assertEqual(result['publishedThrough'],receipt['asOf'])
            self.assertEqual(result['liveComparison']['unpublishedBatchIds'],[next_export['latest']['batchId']])
            self.assertEqual(result['liveComparison']['sealedBatchCount'],2)

    def test_deleted_tail_and_changed_receipt_are_rejected(self):
        current = first_published_batch()
        broken = deepcopy(current)
        broken['batches'] = []
        with self.assertRaisesRegex(ValueError,'head does not match'):
            audit(ROOT,broken)
        broken = deepcopy(current)
        broken['batches'][0]['receiptSha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'Public batch receipt changed'):
            audit(ROOT,broken)

    def test_correct_receipt_hash_cannot_replace_previous_manifest_reference(self):
        catalog = first_published_batch()
        row = catalog['batches'][0]
        receipt = read(ROOT/row['receipt'])
        with TemporaryDirectory() as temp:
            root = Path(temp)
            copytree(ROOT/catalog['seed']['pack'],root/catalog['seed']['pack'])
            copytree(ROOT/row['pack'],root/row['pack'])
            path = root/row['receipt']
            create(path,dict(receipt,previousManifestSha256='0'*64))
            row['receiptSha256'] = sha(path)
            with self.assertRaisesRegex(ValueError,'Broken export chain'):
                audit(root,catalog)
