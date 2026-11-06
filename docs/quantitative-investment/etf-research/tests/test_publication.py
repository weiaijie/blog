"""Crash boundaries and corruption must never publish incomplete run bundles."""
from pathlib import Path
import json,os,subprocess,sys,tempfile,unittest
from etf_research.publication import create,read,sha,seal,promote,lock,verify_bundle
from etf_research.forward import digest,engine_digest

@unittest.skipUnless(sys.platform=='linux','Ubuntu publication contract')
class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.pointer=self.root/'active.json';self.folder=self.root/'bundle'
        self.state=dict(as_of='2026-11-06',engine_sha256=engine_digest());self.state['checkpoint_sha256']=digest(self.state)
        create(self.pointer,dict(as_of='2026-11-05',checkpoint_sha256='prior'))
        create(self.folder/'checkpoint.json',self.state);create(self.root/'input.json',{'verified':True})
        self.new=dict(as_of=self.state['as_of'],checkpoint='bundle/checkpoint.json',checkpoint_sha256=self.state['checkpoint_sha256'])
        create(self.folder/'ready.json',dict(previous_pointer_sha256=sha(self.pointer),input_sha256={'input.json':sha(self.root/'input.json')},pointer=self.new))
        self.before=self.pointer.read_bytes()
    def test_success_and_idempotency(self):
        seal(self.folder);self.assertEqual(promote(self.root,self.folder,self.pointer),'published');after=self.pointer.read_bytes()
        self.assertEqual(promote(self.root,self.folder,self.pointer),'already_published');self.assertEqual(self.pointer.read_bytes(),after)
    def test_partial_run_cannot_publish(self):
        with self.assertRaises(FileNotFoundError):promote(self.root,self.folder,self.pointer)
        self.assertEqual(self.pointer.read_bytes(),self.before)
    def test_corrupt_bundle_rejected(self):
        seal(self.folder);(self.folder/'checkpoint.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'hash'):promote(self.root,self.folder,self.pointer)
        self.assertEqual(self.pointer.read_bytes(),self.before)
    def test_extra_bundle_file_rejected(self):
        seal(self.folder);create(self.folder/'surprise.json',{})
        with self.assertRaisesRegex(ValueError,'file set'):verify_bundle(self.folder)
    def test_input_revision_rejected_on_resume(self):
        seal(self.folder);(self.root/'input.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'Input changed'):promote(self.root,self.folder,self.pointer)
        self.assertEqual(self.pointer.read_bytes(),self.before)
    def test_concurrent_pointer_update_rejected(self):
        seal(self.folder);self.pointer.write_text('{}')
        with self.assertRaisesRegex(ValueError,'Active pointer changed'):promote(self.root,self.folder,self.pointer)
    def test_old_artifacts_never_overwritten(self):
        with self.assertRaises(FileExistsError):create(self.folder/'checkpoint.json',{})
        seal(self.folder)
        with self.assertRaisesRegex(ValueError,'already sealed'):seal(self.folder)
    def test_real_process_death_before_pointer_then_resume(self):
        self.crash('before_pointer');self.assertEqual(self.pointer.read_bytes(),self.before)
        self.assertEqual(promote(self.root,self.folder,self.pointer),'published')
    def test_real_process_death_after_pointer_then_resume(self):
        self.crash('after_pointer');self.assertEqual(read(self.pointer)['as_of'],'2026-11-06')
        self.assertEqual(promote(self.root,self.folder,self.pointer),'already_published')
    def crash(self,stage):
        seal(self.folder)
        code='from etf_research.publication import *; import os,sys; root=Path(sys.argv[1]); promote(root,root/"bundle",root/"active.json",lambda stage: os._exit(71) if stage==sys.argv[2] else None)'
        r=subprocess.run([sys.executable,'-c',code,str(self.root),stage]);self.assertEqual(r.returncode,71)
    def test_lock_excludes_second_process_and_releases_on_exit(self):
        path=self.root/'run.lock'
        code='from etf_research.publication import lock; import sys;\nwith lock(sys.argv[1]): pass'
        with lock(path):
            p=subprocess.run([sys.executable,'-c',code,str(path)],capture_output=True);self.assertNotEqual(p.returncode,0)
        self.assertEqual(subprocess.run([sys.executable,'-c',code,str(path)]).returncode,0)
if __name__=='__main__':unittest.main()
