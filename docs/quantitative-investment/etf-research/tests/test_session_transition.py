"""Exercise promotion evidence independently of a future live trading day."""
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch
from hashlib import sha256
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import check_session_transition as audit
from run_scheduled import timer_context
from etf_research.publication import create, encoded, sha, seal


@unittest.skipUnless(sys.platform=='linux','Sealing uses the Ubuntu filesystem contract')
class TransitionEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.bundle=self.root/'reports/daily/example'
        self.op=self.root/'reports/operations/example'
        self.time='2026-11-06T08:10:00+00:00'
        self.before={'checkpoint':'prior.json','checkpoint_sha256':'old'}
        pointer={'checkpoint_sha256':'new','bundle':'reports/daily/example'}
        create(self.bundle/'ready.json',dict(pointer=pointer,previous_pointer_sha256=sha256(encoded(self.before)).hexdigest()))
        create(self.bundle/'started.json',dict(created_at_shanghai=self.time,previous_checkpoint='prior.json'))
        seal(self.bundle)
        self.after=dict(pointer,bundle_manifest_sha256=sha(self.bundle/'manifest.json'))
        for n in ('example-prices','example-official'):
            create(self.root/'data/snapshots'/n/'requests.json',[dict(requested_at_utc=self.time)])
        self.report=dict(target='2026-11-06',sessions_appended=['2026-11-06'],offline=False,
                         checkpoint='new',prices='example-prices',official='example-official',status='replayed_extension')
        self.result=dict(started_at_utc=self.time,finished_at_utc=self.time,mode='scheduled',phase='success',exit_code=0,
                         operation='reports/operations/example',account_through='2026-11-06',account_changed=True,
                         account_before=self.before,account_after=self.after,checkpoint_sha256='new',
                         result=dict(status='published',as_of='2026-11-06',bundle='reports/daily/example'),
                         systemd_trigger=timer_context({'TRIGGER_UNIT':'etf-research-daily.timer','INVOCATION_ID':'1'*32}))

    def inspect(self):
        create(self.op/'started.json',dict(started_at_utc=self.time,operation=self.result['operation'],mode=self.result['mode']))
        create(self.op/'result.json',self.result)
        seal(self.op)
        with patch.object(audit,'ROOT',self.root),patch.object(audit,'check_bundle',return_value=self.report):
            return audit.check_operation(self.op)

    def test_observed_timer_and_bound_publication(self):
        self.assertEqual(self.inspect()['status'],'timer_published_new_sessions')

    def test_manual_supervisor_lacks_timer_evidence(self):
        self.result['systemd_trigger']=timer_context({})
        self.assertNotEqual(self.inspect()['status'],'timer_published_new_sessions')

    def test_different_published_pointer_rejected(self):
        self.result['account_after']={**self.after,'checkpoint_sha256':'another'}
        with self.assertRaisesRegex(ValueError,'pointers differ'):
            self.inspect()

    def test_replay_cannot_prove_unattended_collection(self):
        self.report['offline']=True
        self.assertNotEqual(self.inspect()['status'],'timer_published_new_sessions')

    def test_wrong_capture_time_rejected(self):
        path=self.root/'data/snapshots/example-prices/requests.json'
        path.write_bytes(encoded([dict(requested_at_utc='2026-11-06T08:09:59+00:00')]))
        with self.assertRaisesRegex(ValueError,'Capture timestamps outside'):
            self.inspect()

    def test_noop_requires_matching_snapshots_of_pointer(self):
        self.result.update(account_changed=False, result=dict(status='up_to_date',as_of='2026-11-06',
                           network_requests=0,account_changes=0))
        with self.assertRaisesRegex(ValueError,'No-op changed'):
            self.inspect()
