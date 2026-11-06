from pathlib import Path
import hashlib, sys, tempfile, unittest
from unittest.mock import patch
from etf_research.evidence_archive import capture, verify, restore, compare, object_path, safe_path, inventory
from etf_research.publication import create, read, encoded

@unittest.skipUnless(sys.platform=='linux','Ubuntu archive locks')
class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.root=self.base/'project';self.store=self.base/'archive'
        create(self.root/'evidence.json',{'public':'one'})
    def snapshot(self):return capture(self.root,self.store,['evidence.json'])['snapshot']
    def test_incremental_and_new_directory_restore(self):
        first=self.snapshot();second=capture(self.root,self.store,['evidence.json']);self.assertEqual(second['new_objects'],0)
        result=restore(self.store,first,self.base/'recovered');self.assertEqual(result['verified_files'],1)
        self.assertEqual((self.base/'recovered/evidence.json').read_bytes(),(self.root/'evidence.json').read_bytes())
    def test_destination_conflict_no_overwrite(self):
        identity=self.snapshot();before=(self.root/'evidence.json').read_bytes()
        with self.assertRaises(ValueError):restore(self.store,identity,self.root)
        self.assertEqual((self.root/'evidence.json').read_bytes(),before)
    def test_corrupt_object_rejected_before_destination_created(self):
        identity=self.snapshot();snap=verify(self.store,identity);obj=object_path(self.store,snap['files']['evidence.json']['sha256']);obj.write_bytes(b'bad')
        with self.assertRaises(ValueError):restore(self.store,identity,self.base/'restore')
        self.assertFalse((self.base/'restore').exists())
        with self.assertRaises(ValueError):self.snapshot()
    def test_changed_snapshot_manifest_rejected(self):
        identity=self.snapshot();(self.store/'snapshots'/f'{identity}.json').write_text('{}')
        with self.assertRaises(ValueError):verify(self.store,identity)
    def test_malicious_paths_rejected(self):
        for name in ['../escape','/absolute','C:/secret','a\\b','a/../b','a//b']:
            with self.subTest(name=name),self.assertRaises(ValueError):safe_path(self.root,name)
    def test_symlink_rejected(self):
        (self.root/'link').symlink_to(self.base,target_is_directory=True)
        with self.assertRaises(ValueError):safe_path(self.root,'link/elsewhere')
    def test_compare_reports_conflict_without_write(self):
        identity=self.snapshot();(self.root/'evidence.json').write_bytes(b'changed')
        result=compare(self.store,identity,self.root);self.assertEqual(result['conflicts'],['evidence.json']);self.assertEqual(result['writes_performed'],0)
    def test_store_inside_project_rejected(self):
        with self.assertRaises(ValueError):capture(self.root,self.root/'backup',['evidence.json'])
    def test_private_runtime_file_blocked(self):
        create(self.root/'config/archive_inventory.json',{'files':['evidence.json']})
        create(self.root/'reports/operations/x/.env',{'secret':'fixture'})
        with self.assertRaises(ValueError):inventory(self.root)
    def test_missing_object_rejected(self):
        identity=self.snapshot();snap=verify(self.store,identity)
        object_path(self.store,snap['files']['evidence.json']['sha256']).unlink()
        with self.assertRaises(FileNotFoundError):restore(self.store,identity,self.base/'restore')
    def test_interrupted_capture_never_creates_a_complete_snapshot(self):
        with patch('etf_research.evidence_archive.sync_dir',side_effect=InterruptedError('test interruption')):
            with self.assertRaises(InterruptedError):self.snapshot()
        self.assertFalse((self.store/'snapshots').exists())
        result=capture(self.root,self.store,['evidence.json'])
        self.assertEqual(result['new_objects'],0);verify(self.store,result['snapshot'])
    def test_incomplete_object_is_never_published(self):
        with patch('etf_research.evidence_archive.os.link',side_effect=InterruptedError('before object publish')):
            with self.assertRaises(InterruptedError):self.snapshot()
        self.assertFalse((self.store/'snapshots').exists())
        self.assertFalse(any(p.is_file() and len(p.name)==64 for p in (self.store/'objects').rglob('*')))
        identity=self.snapshot();verify(self.store,identity)
