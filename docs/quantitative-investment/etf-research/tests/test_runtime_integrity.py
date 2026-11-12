"""Live status may advance, but it must still point to sealed verified records."""
from pathlib import Path
from unittest.mock import patch
import contextlib,hashlib,io,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import verify_project
from etf_research.publication import create,read,sha,seal

@unittest.skipUnless(sys.platform=='linux','Ubuntu runtime integrity')
class RuntimeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        create(self.root/'data/snapshots/example/body.json',{'source':'fixture'})
        create(self.root/'data/snapshots/example/manifest.json',{'body.json':sha(self.root/'data/snapshots/example/body.json')})
        create(self.root/'immutable.json',{'code':'fixture'})
        create(self.root/'reports/2026-11-12-workbench/manifest.json',{'immutable.json':sha(self.root/'immutable.json')})
        state=read(ROOT/'reports/2026-11-06-close/forward_checkpoint.json')
        folder=self.root/'reports/daily/example';create(folder/'forward_checkpoint.json',state);seal(folder)
        create(self.root/'config/active_run.json',dict(as_of=state['as_of'],checkpoint_sha256=state['checkpoint_sha256'],checkpoint='reports/daily/example/forward_checkpoint.json',bundle='reports/daily/example',bundle_manifest_sha256=sha(folder/'manifest.json')))
    def verify(self):
        with patch.object(verify_project,'ROOT',self.root),contextlib.redirect_stdout(io.StringIO()):verify_project.main()
    def status(self,name):
        folder=self.root/'reports/operations'/name;result=dict(phase='success',operation=str(folder.relative_to(self.root)))
        create(folder/'result.json',result);seal(folder)
        p=self.root/'site/operation_status.json';p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(result))
    def test_new_live_operation_is_valid_without_rewriting_static_manifest(self):
        self.status('one');self.verify();self.status('two');self.verify()
    def test_status_not_matching_sealed_result_rejected(self):
        self.status('one');p=self.root/'site/operation_status.json';r=read(p);r['phase']='failed';p.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError,'sealed record'):self.verify()
    def test_corrupt_current_checkpoint_rejected(self):
        (self.root/'reports/daily/example/forward_checkpoint.json').write_text('{}')
        with self.assertRaises((ValueError,KeyError)):self.verify()
    def test_static_inputs_remain_hash_protected(self):
        (self.root/'immutable.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'Hash mismatch'):self.verify()
    def test_health_pointer_must_match_sealed_observation(self):
        observation='reports/health/one';result=dict(observation=observation,state='current')
        create(self.root/observation/'result.json',result);seal(self.root/observation)
        create(self.root/'site/health_status.json',dict(result,state='market_closed'))
        with self.assertRaisesRegex(ValueError,'Health status'):self.verify()
if __name__=='__main__':unittest.main()
