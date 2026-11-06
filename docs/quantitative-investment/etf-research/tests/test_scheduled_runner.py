"""Scheduled supervision must preserve failure evidence and honest status."""
from pathlib import Path
from unittest.mock import patch
import json,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import run_scheduled
from etf_research.publication import create,read,verify_bundle

@unittest.skipUnless(sys.platform=='linux','Ubuntu supervisor')
class ScheduledTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        create(self.root/'config/active_run.json',dict(as_of='2026-11-06',checkpoint_sha256='frozen'))
        create(self.root/'config/collection.json',read(ROOT/'config/collection.json'))
    def run_it(self,runner):
        with patch.object(run_scheduled,'client_version',return_value='curl test'),patch.object(run_scheduled,'scheduler_state',return_value={'timer_enabled':'enabled','timer_active':'active','linger':'yes'}):return run_scheduled.supervise(self.root,runner=runner)
    def success(self,root,refresh,out,err):out.write(b'{"status":"up_to_date","network_requests":0}\n');return 0
    def test_success_sealed_and_checkpoint_not_changed(self):
        result=self.run_it(self.success);self.assertEqual(result['phase'],'success');self.assertFalse(result['account_changed'])
        verify_bundle(self.root/result['operation']);self.assertEqual(read(self.root/'site/operation_status.json'),result)
    def test_failure_keeps_prior_success_and_stderr(self):
        prior=self.run_it(self.success)
        def failed(root,refresh,out,err):err.write(b'official catalog changed\n');return 1
        result=self.run_it(failed);self.assertEqual(result['phase'],'failed');self.assertEqual(result['last_success'],prior['last_success']);self.assertFalse(result['account_changed'])
        self.assertIn('official catalog changed',(self.root/result['operation']/'stderr.log').read_text());verify_bundle(self.root/result['operation'])
    def test_child_timeout_keeps_partial_logs(self):
        def failed(root,refresh,out,err):out.write(b'partial output');raise subprocess.TimeoutExpired('pipeline',780)
        result=self.run_it(failed);self.assertEqual(result['exit_code'],124);self.assertEqual(result['phase'],'failed');verify_bundle(self.root/result['operation'])
    def test_exit_zero_without_result_is_not_success(self):
        result=self.run_it(lambda *a:0);self.assertEqual(result['phase'],'failed');self.assertIsNone(result['last_success'])
    def test_missing_dependency_failure_is_recorded(self):
        with patch.object(run_scheduled,'client_version',side_effect=FileNotFoundError('curl missing')),patch.object(run_scheduled,'scheduler_state',return_value={}):result=run_scheduled.supervise(self.root,runner=lambda *a:self.fail('No child'))
        self.assertEqual(result['phase'],'failed');verify_bundle(self.root/result['operation'])
    def test_orphan_operation_is_reported_without_rewriting_it(self):
        create(self.root/'reports/operations/prior/started.json',{'old':'unfinished'})
        result=self.run_it(self.success);self.assertIn('reports/operations/prior',result['unfinished_prior_operations']);self.assertFalse((self.root/'reports/operations/prior/result.json').exists())
    def test_pointer_corruption_prevents_false_success(self):
        def broken(root,refresh,out,err):(root/'config/active_run.json').write_text('not-json');out.write(b'{"status":"up_to_date"}\n');return 0
        result=self.run_it(broken);self.assertEqual(result['phase'],'failed');self.assertIsNone(result['account_through'])
    def test_interrupt_can_report_pointer_already_changed(self):
        def interrupted(root,refresh,out,err):
            (root/'config/active_run.json').write_text(json.dumps(dict(as_of='2026-11-09',checkpoint_sha256='new')));raise InterruptedError('terminated after publish')
        result=self.run_it(interrupted);self.assertEqual(result['phase'],'failed');self.assertTrue(result['account_changed']);self.assertEqual(result['account_through'],'2026-11-09')
if __name__=='__main__':unittest.main()
