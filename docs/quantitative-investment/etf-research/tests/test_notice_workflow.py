from pathlib import Path
from copy import deepcopy
import tempfile, unittest
from etf_research.notice_workflow import validate_decision, validate_packet
from etf_research.notice_review import prepare_review
from etf_research.publication import sha

ROOT=Path(__file__).resolve().parents[1]
class ReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'notice.body').write_bytes(b'official text fixture')
        self.packet={'packet_sha256':'packet-a','changes':[{'change_id':'change-a'}]}
        self.decision={'packet_sha256':'packet-a','reviews':[{'change_id':'change-a','conclusion':'no_account_effect',
            'rationale':'Test fixture only','full_text_checked':True,'effective_dates':['2026-11-06'],
            'evidence':[{'path':'notice.body','sha256':sha(self.root/'notice.body'),'locator':'page 1'}]}]}
    def test_evidence_bound_review(self):self.assertEqual(len(validate_decision(self.root,self.packet,self.decision)),1)
    def test_old_decision_cannot_review_new_packet(self):
        self.decision['packet_sha256']='other'
        with self.assertRaises(ValueError):validate_decision(self.root,self.packet,self.decision)
    def test_unknown_change_rejected(self):
        self.decision['reviews'][0]['change_id']='other'
        with self.assertRaises(ValueError):validate_decision(self.root,self.packet,self.decision)
    def test_changed_evidence_rejected(self):
        (self.root/'notice.body').write_bytes(b'revised')
        with self.assertRaises(ValueError):validate_decision(self.root,self.packet,self.decision)
    def test_title_only_or_empty_evidence_rejected(self):
        for field,value in [('full_text_checked',False),('evidence',[]),('rationale','')]:
            d=deepcopy(self.decision);d['reviews'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_decision(self.root,self.packet,d)
    def test_no_approval_conclusion(self):
        self.decision['reviews'][0]['conclusion']='approved'
        with self.assertRaises(ValueError):validate_decision(self.root,self.packet,self.decision)
    def test_current_real_packet_is_unchanged(self):
        packet=prepare_review(ROOT/'data/snapshots','20261106T192520-fbb0790c-prices')
        validate_packet(ROOT,packet);self.assertEqual(packet['changes'],[]);self.assertFalse(packet['approves_prices_or_events'])
