import contextlib
import copy
import io
from pathlib import Path
import tempfile
import unittest

import auto_lab as auto
from test_reply_lab import row


def fixture(run):
    packets = [
        {'id':'dev','chat_id':'a','date':'2026-03-01','split':'dev','channel':'私聊',
         'context':[{'role':'对方','speaker':'对方1','text':'接口字段改好了吗'}], 'reference':['学习答案']},
        {'id':'eval','chat_id':'b','date':'2026-03-02','split':'eval','channel':'群聊',
         'context':[{'role':'对方','speaker':'对方2','text':'<script>别执行</script> 接口改好了吗'}]}
    ]
    source = [{**p,'reference':p.get('reference',['隐藏答案']), 'identity_verified':True} for p in packets]
    analysis = {'input_sha256':auto.sha(packets),'reviewer_kind':'ai','reviewer':'测试执行器',
                'items':[{'id':p['id'],'scene':'工作','reply_state':'待判断','quality':'usable',
                          'confidence':'medium','evidence_indices':[1],'reason':'接口文字',
                          'draft':['测试草稿']} for p in packets]}
    for name,value in [('analysis-inputs.json',packets),('source.private.json',source),
                       ('ai-analysis.json',analysis),
                       ('manifest.json',{'input_sha256':auto.sha(packets),'source_sha256':auto.sha(source)})]:
        auto.lab.write_json(run/name,value)
    return packets, source, analysis


class AutoLabTests(unittest.TestCase):
    def test_expanded_context_preserves_media_speakers_and_excludes_target_future(self):
        messages=[row('other','前文接口',1),row('third','不可见图片',2,'image'),
                  row('','系统内容',3,'system'),row('other','可以么',4),
                  row('me','目标文字',5),row('other','未来',6)]
        candidates=auto.lab.make_candidates(messages,'me',min_reply_chars=1)
        expanded=auto.expand_context(candidates[0],messages,'me')
        text=str(expanded['context'])
        self.assertIn('前文接口',text)
        self.assertIn('[缺失image内容]',text)
        self.assertIn('对方2',text)
        self.assertIn('未知发送者',text)
        for forbidden in ('目标文字','未来','不可见图片','系统内容'):
            self.assertNotIn(forbidden,text)
        self.assertTrue(all(s['sender_username'] for s in expanded['source']))

    def test_expansion_keeps_time_boundary(self):
        messages=[row('other','太早',1),row('other','当前',2000),row('me','回复',2001)]
        sample=auto.lab.make_candidates(messages,'me',min_reply_chars=1)[0]
        self.assertNotIn('太早',str(auto.expand_context(sample,messages,'me')['context']))

    def test_ai_lane_needs_no_user_flags_and_hides_answers(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder)
            fixture(run)
            auto.assemble(run)
            for name in ('eval-inputs.json','predictions.json'):
                text=(run/name).read_text(encoding='utf-8')
                self.assertNotIn('隐藏答案',text)
                self.assertNotIn('reference',text)
            page=(run/'results.html').read_text(encoding='utf-8')
            self.assertNotIn('<script>',page)
            self.assertIn('&lt;script&gt;',page)
            self.assertIn('对方2',page)
            self.assertNotIn('<input',page)
            with self.assertRaisesRegex(ValueError,'冻结'):
                auto.assemble(run)

    def test_analysis_rejects_missing_duplicate_hash_and_foreign_state(self):
        with tempfile.TemporaryDirectory() as folder:
            packets,_,analysis=fixture(Path(folder))
            cases=[]
            altered=copy.deepcopy(analysis);altered['items'].pop();cases.append(altered)
            altered=copy.deepcopy(analysis);altered['items'][1]['id']='dev';cases.append(altered)
            altered=copy.deepcopy(analysis);altered['input_sha256']='wrong';cases.append(altered)
            altered=copy.deepcopy(analysis);altered['items'][1]['evidence_indices']=[2];cases.append(altered)
            altered=copy.deepcopy(analysis);altered['items'][1]['reply_state']='暂时没空';cases.append(altered)
            altered=copy.deepcopy(altered);altered['items'][1]['state_evidence_indices']=[1];cases.append(altered)
            altered=copy.deepcopy(analysis);altered['items'][1]['draft']=[];cases.append(altered)
            for case in cases:
                with self.subTest(case=case),self.assertRaises(ValueError):
                    auto.validate_analysis(packets,case)

    def test_source_changes_and_cross_split_chat_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder)
            packets,source,analysis=fixture(run)
            source[0]['reference']=['被修改的答案']
            auto.lab.write_json(run/'source.private.json',source)
            with self.assertRaisesRegex(ValueError,'修改'):
                auto.assemble(run)
            packets,source,analysis=fixture(run)
            packets[1]['chat_id']='a';source[1]['chat_id']='a'
            analysis['input_sha256']=auto.sha(packets)
            for name,value in [('analysis-inputs.json',packets),('source.private.json',source),
                               ('ai-analysis.json',analysis),
                               ('manifest.json',{'input_sha256':auto.sha(packets),'source_sha256':auto.sha(source)})]:
                auto.lab.write_json(run/name,value)
            with self.assertRaisesRegex(ValueError,'同一会话'):
                auto.assemble(run)

    def test_evaluation_must_cover_frozen_predictions_and_cannot_claim_human(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);fixture(run);auto.assemble(run)
            assessment={'comparison_sha256':auto.sha(auto.lab.read_json(run/'comparison.private.json')),
                        'reviewer_kind':'ai','reviewer':'测试执行器','items':[
                            {'id':'eval','style':'贴近','meaning':'不同','unsupported_fact':False,
                             'extra_commitment':False,'verdict':'测试','reason':'分别看口吻和语义'}]}
            auto.lab.write_json(run/'ai-evaluation.json',assessment)
            auto.evaluate(run)
            self.assertEqual(auto.lab.read_json(run/'evaluation-report.json')['human_ratings'],0)
            for altered in ({**assessment,'items':[]},{**assessment,'items':assessment['items']*2},
                            {**assessment,'comparison_sha256':'wrong'},{**assessment,'reviewer_kind':'human'}):
                auto.lab.write_json(run/'ai-evaluation.json',altered)
                with self.assertRaises(ValueError):auto.evaluate(run)
            auto.lab.write_json(run/'ai-evaluation.json',assessment)
            auto.lab.write_json(run/'predictions.json',[{'id':'eval','draft':['事后修改']}])
            with self.assertRaisesRegex(ValueError,'不匹配'):auto.evaluate(run)
            with self.assertRaisesRegex(ValueError,'改变'):auto.render(run)

    def test_request_retrieves_dev_only_and_rejects_contamination(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);fixture(run);auto.assemble(run)
            auto.build_request(run,'接口字段需要改吗',run/'request.json')
            request=auto.lab.read_json(run/'request.json')
            self.assertEqual(request['provenance']['example_ids'],['dev'])
            self.assertNotIn('隐藏答案',str(request))
            self.assertFalse(request['network_called'])
            contaminated=auto.lab.read_json(run/'dev.json')
            contaminated[0]['id']='eval'
            auto.lab.write_json(run/'dev.json',contaminated)
            with self.assertRaisesRegex(ValueError,'开发组'):
                auto.build_request(run,'接口',run/'bad.json')


if __name__=='__main__':
    with contextlib.redirect_stdout(io.StringIO()):
        unittest.main()
