"""Run the real admission gate inside the publication orchestrator."""
from pathlib import Path
from datetime import datetime,date
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json,shutil,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import run_daily
from etf_research.publication import create,read,sha

class Clock(datetime):
    @classmethod
    def now(cls,tz=None):return cls(2026,11,6,18,tzinfo=tz)

@unittest.skipUnless(sys.platform=='linux','Ubuntu pipeline contract')
class DailyPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        snapshots=self.root/'data/snapshots';snapshots.mkdir(parents=True)
        for path in (ROOT/'data/snapshots').iterdir():
            if path.is_dir():shutil.copytree(path,snapshots/path.name)
        self.candidate=snapshots/'synthetic-test-only'
        shutil.copytree(ROOT/'data/snapshots/2026-11-06-close-windows-1653',self.candidate)
        state=read(ROOT/'reports/2026-11-06-close/forward_checkpoint.json')
        create(self.root/'prior.json',state);create(self.root/'active.json',dict(as_of=state['as_of'],checkpoint='prior.json',checkpoint_sha256=state['checkpoint_sha256']))
        self.before=(self.root/'active.json').read_bytes()
        self.args=SimpleNamespace(pointer='active.json',through=date(2026,11,6),candidate='synthetic-test-only',official='2026-11-06-official-close-1650',rebuild=True,resume=None,retry_of=None)
    def resign(self):
        index=self.candidate/'requests.json';rows=read(index)
        for r in rows:r['sha256']=sha(self.candidate/(r['name']+'.body'))
        index.write_text(json.dumps(rows))
        m={p.name:sha(p) for p in self.candidate.iterdir() if p.is_file() and p.name!='manifest.json'}
        (self.candidate/'manifest.json').write_text(json.dumps(m))
    def execute(self):
        with patch.object(run_daily,'ROOT',self.root),patch.object(run_daily,'datetime',Clock):return run_daily.run(self.args)
    def rejected(self,pattern):
        with self.assertRaisesRegex(ValueError,pattern):self.execute()
        self.assertEqual((self.root/'active.json').read_bytes(),self.before)
        failed=list((self.root/'reports/daily').glob('*/failure.json'));self.assertTrue(failed)
        self.assertFalse(any((p.parent/'ready.json').exists() for p in failed))
        return failed
    def test_failed_http_retained_without_account_change(self):
        index=self.candidate/'requests.json';rows=read(index);rows[0]['status']=503;index.write_text(json.dumps(rows));self.resign()
        self.rejected('Failed/mismatched')
    def test_changed_notice_retained_without_account_change(self):
        p=self.candidate/'catalog_510300.body';data=read(p);data['result'][0]['TITLE']+='(test revision)';data['pageHelp']['data']=data['result'];p.write_text(json.dumps(data));self.resign()
        failed=self.rejected('catalog changed')[0]
        review=read(failed)['review_packet']
        from etf_research.notice_workflow import review_queue
        self.assertTrue((self.root/review/'packet.json').exists())
        self.assertEqual(review_queue(self.root)[0]['pending_changes'],1)
        from etf_research.notice_workflow import save_decision
        packet=read(self.root/review/'packet.json')
        decision=dict(packet_sha256=packet['packet_sha256'],reviews=[dict(change_id=packet['changes'][0]['change_id'],conclusion='unresolved',rationale='Synthetic test remains unresolved',evidence=[])])
        result=save_decision(self.root,review,decision)
        self.assertFalse(result['approves_prices_or_events']);self.assertEqual(review_queue(self.root)[0]['pending_changes'],1)
        self.assertEqual((self.root/'active.json').read_bytes(),self.before)
    def test_source_tamper_without_resign_is_blocked(self):
        (self.candidate/'sina_510300.body').write_bytes(b'corrupt test fixture')
        self.rejected('hash|Hash|checksum')
    def test_retry_preserves_failed_run(self):
        (self.candidate/'sina_510300.body').write_bytes(b'corrupt test fixture')
        prior=self.rejected('hash|Hash|checksum')[0];before=prior.read_bytes();self.args.retry_of=str(prior.parent.relative_to(self.root))
        self.rejected('hash|Hash|checksum');self.assertEqual(prior.read_bytes(),before)
        self.assertEqual(len(list((self.root/'reports/daily').glob('*/failure.json'))),2)
    def test_noop_does_not_fetch_or_create_run(self):
        self.args.rebuild=False
        with patch.object(run_daily.subprocess,'run',side_effect=AssertionError('unexpected network')):
            self.assertEqual(self.execute()['status'],'up_to_date')
        self.assertFalse((self.root/'reports/daily').exists());self.assertEqual((self.root/'active.json').read_bytes(),self.before)
    def test_future_date_cannot_publish(self):
        self.args.through=date(2026,11,9)
        with self.assertRaisesRegex(ValueError,'completed'):self.execute()
        self.assertEqual((self.root/'active.json').read_bytes(),self.before)
    def test_active_state_corruption_blocks_even_noop(self):
        self.args.rebuild=False;(self.root/'prior.json').write_text(json.dumps(dict(read(self.root/'prior.json'),as_of='2026-11-05')))
        with self.assertRaisesRegex(ValueError,'integrity'):self.execute()
if __name__=='__main__':unittest.main()
