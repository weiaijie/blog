from pathlib import Path
from shutil import copytree
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from audit_observation_repository import CATALOG, audit
from etf_research.publication import create, read, sha
from prepare_observation_publication import prepare


class PrepareObservationPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work=Path(temporary.name)
        current=read(ROOT/CATALOG)
        self.row=current['batches'][0]
        self.original=ROOT/self.row['receipt']
        self.receipt=read(self.original)
        self.spool=self.work/'spool'
        batch=self.spool/'batches'/self.row['batchId']
        copytree(ROOT/self.row['pack'],batch/'pack')
        (batch/'receipt.json').write_bytes(self.original.read_bytes())
        create(batch/'started.json',{key:self.receipt[key] for key in ('asOf','after','trigger')})
        self.before=dict(current,batches=[],head=dict(batchId=None,manifestSha256=current['seed']['manifestSha256']))
        self.after=dict(current,batches=[self.row],head=dict(batchId=self.row['batchId'],
                                                            manifestSha256=self.receipt['packManifestSha256']))

    def test_staged_release_is_byte_identical_and_can_be_restored(self):
        catalog=self.work/'before.json'
        create(catalog,self.before)
        stage=self.work/'prepared'
        result=prepare(ROOT,self.spool,stage,catalog_path=catalog)
        patched=read(stage/CATALOG)
        batch=patched['batches'][0]
        self.assertEqual(result['baseCatalogSha256'],sha(catalog))
        self.assertEqual(result['preparedCatalogSha256'],sha(stage/CATALOG))
        self.assertEqual(result['unpublishedBatchIds'],[self.row['batchId']])
        self.assertEqual(result['preparedManifestSha256'],self.receipt['packManifestSha256'])
        self.assertEqual(read(catalog),self.before)
        self.assertEqual((stage/batch['receipt']).read_bytes(),self.original.read_bytes())
        seed=self.before['seed']['pack']
        copytree(ROOT/seed,stage/seed)
        checked=audit(stage,patched,live_spool=self.spool,destination=self.work/'restored')
        self.assertEqual(checked['liveComparison']['unpublishedBatchIds'],[])
        self.assertEqual(checked['restored']['receipts']['observation'],11)

    def test_no_new_batch_creates_no_output_and_divergent_history_is_rejected(self):
        catalog=self.work/'after.json'
        create(catalog,self.after)
        stage=self.work/'prepared'
        self.assertEqual(prepare(ROOT,self.spool,stage,catalog_path=catalog)['status'],'up_to_date')
        self.assertFalse(stage.exists())
        path=self.spool/'batches'/self.row['batchId']/'receipt.json'
        path.write_text('{}',encoding='utf-8')
        with self.assertRaises((ValueError,KeyError)):
            prepare(ROOT,self.spool,stage,catalog_path=catalog)
        self.assertFalse(stage.exists())
