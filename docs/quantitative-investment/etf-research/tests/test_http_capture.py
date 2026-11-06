"""Transport retry policy cannot erase failures or weaken semantic admission."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json,subprocess,tempfile,unittest
from etf_research.http_capture import fetch,load_policy,retry_delay,capture_attempt
ROOT=Path(__file__).resolve().parents[1]
URL='https://query.sse.com.cn/commonQuery.do?SECURITY_CODE=510300'

class HttpCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name);self.policy=load_policy()
    def attempt(self,statuses):
        outcomes=iter(statuses)
        def call(folder,name,url,policy):
            code,status=next(outcomes);body=(str(status)+':'+name).encode();(folder/(name+'.body')).write_bytes(body)
            r=dict(name=name,url=url,curl_exit=code,status=status,sha256=hashlib.sha256(body).hexdigest())
            if code or status!=200:r['error']='test failure'
            return r
        return call
    def test_503_then_success_preserves_both_attempts(self):
        waits=[];r=fetch(self.folder,'catalog_510300',URL,self.policy,attempt_fn=self.attempt([(0,503),(0,200)]),sleep=waits.append)
        self.assertEqual(waits,[2]);self.assertEqual(r['actual_requests'],2);self.assertNotIn('error',r)
        self.assertEqual((self.folder/'catalog_510300.body').read_bytes(),(self.folder/'catalog_510300_attempt_02.body').read_bytes())
        self.assertTrue((self.folder/'catalog_510300_attempt_01.body').read_bytes().startswith(b'503'))
    def test_timeout_is_bounded_and_failure_remains_selected(self):
        waits=[];r=fetch(self.folder,'catalog_510300',URL,self.policy,attempt_fn=self.attempt([(28,0)]*3),sleep=waits.append)
        self.assertEqual(waits,[2,4]);self.assertEqual(r['actual_requests'],3);self.assertIn('error',r)
    def test_certificate_failure_not_retried(self):
        waits=[];r=fetch(self.folder,'catalog_510300',URL,self.policy,attempt_fn=self.attempt([(60,0)]),sleep=waits.append)
        self.assertEqual(r['actual_requests'],1);self.assertEqual(waits,[])
    def test_404_not_retried(self):
        r=fetch(self.folder,'catalog_510300',URL,self.policy,attempt_fn=self.attempt([(0,404)]),sleep=lambda _:self.fail('No retry'))
        self.assertEqual(r['actual_requests'],1)
    def test_200_body_is_not_declared_admitted(self):
        r=fetch(self.folder,'catalog_510300',URL,self.policy,attempt_fn=self.attempt([(0,200)]))
        self.assertNotIn('admitted',r);self.assertEqual(r['actual_requests'],1)
    def test_retry_after_is_respected_or_deferred_to_next_job(self):
        row=dict(curl_exit=0,status=429,retry_after_seconds=12)
        self.assertEqual(retry_delay(row,self.policy,0),12)
        self.assertIsNone(retry_delay({**row,'retry_after_seconds':120},self.policy,0))
    def test_old_evidence_cannot_be_overwritten(self):
        (self.folder/'catalog_510300.body').write_bytes(b'original')
        with self.assertRaises(FileExistsError):fetch(self.folder,'catalog_510300',URL,self.policy,attempt_fn=lambda *a:self.fail('No request'))
        self.assertEqual((self.folder/'catalog_510300.body').read_bytes(),b'original')
    def test_url_credentials_or_wrong_host_rejected(self):
        for url in ['http://query.sse.com.cn/','https://example.com/','https://user:secret@query.sse.com.cn/']:
            with self.assertRaisesRegex(ValueError,'URL'):fetch(self.folder,'catalog',url,self.policy)
    def test_unsafe_name_rejected(self):
        with self.assertRaisesRegex(ValueError,'name'):fetch(self.folder,'../outside',URL,self.policy)
    def test_limits_cannot_be_unbounded(self):
        p=self.folder/'policy.json';p.write_text(json.dumps({**self.policy,'max_attempts':100}))
        with self.assertRaisesRegex(ValueError,'bound'):load_policy(p)
    def test_curl_keeps_tls_checks_and_ipv4_and_captures_metrics(self):
        def process(command,**kwargs):
            self.assertEqual(command[:2],['curl','--disable']);self.assertIn('--ipv4',command)
            self.assertNotIn('--insecure',command);self.assertNotIn('-k',command);self.assertNotIn('--location',command)
            Path(command[command.index('--output')+1]).write_bytes(b'upstream unavailable')
            Path(command[command.index('--dump-header')+1]).write_text('HTTP/1.1 503 Service Unavailable\nRetry-After: 12\n')
            return SimpleNamespace(returncode=0,stderr='',stdout=json.dumps(dict(response_code=503,ssl_verify_result=0,remote_ip='202.122.113.77')))
        with patch('etf_research.http_capture.client_version',return_value='curl test'),patch('etf_research.http_capture.subprocess.run',side_effect=process):
            r=capture_attempt(self.folder,'attempt',URL,self.policy)
        self.assertEqual(r['status'],503);self.assertEqual(r['retry_after_seconds'],12);self.assertEqual(r['sha256'],hashlib.sha256(b'upstream unavailable').hexdigest());self.assertIn('error',r)
    def test_hung_child_keeps_partial_body_and_failure(self):
        def hung(command,**kwargs):
            Path(command[command.index('--output')+1]).write_bytes(b'partial');raise subprocess.TimeoutExpired(command,30)
        with patch('etf_research.http_capture.client_version',return_value='curl test'),patch('etf_research.http_capture.subprocess.run',side_effect=hung):
            r=capture_attempt(self.folder,'attempt',URL,self.policy)
        self.assertEqual(r['curl_exit'],124);self.assertEqual((self.folder/'attempt.body').read_bytes(),b'partial');self.assertIn('error',r)
if __name__=='__main__':unittest.main()
