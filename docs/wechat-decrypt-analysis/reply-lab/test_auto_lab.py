import contextlib
import copy
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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
    def test_scene_development_excludes_existing_evaluation_contacts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=[];own=[]
            for index,chat in enumerate(('dev-chat','eval-chat')):
                incoming={**row('other','下班到家吃饭了吗',10+index*10),'chat_username':chat}
                source.append(incoming)
                for offset in (1,2,3):
                    sent={**row('me','恩到了',10+index*10+offset),'chat_username':chat}
                    own.append(sent);source.append(sent)
            for s in source:
                s.update({k:'' for k in ('chat_name','remark','nick_name','alias','sender_label')})
            with patch.object(auto.lab,'HERE',root),patch.object(auto,'used_history',return_value=(set(),set(),{auto.lab.digest('eval-chat'):'eval'})), \
                 patch.object(auto.lab,'rows',side_effect=lambda path:iter(own if path.name=='self_messages_cleaned.csv' else source)), \
                 patch.object(auto.lab,'read_json',return_value={'db_dir':'C:/fake/me/db_storage'}), \
                 patch.object(auto.lab,'verify_identity',return_value=True):
                auto.prepare(root/'scene-run',scene_development=True)
            packets=auto.lab.read_json(root/'scene-run/analysis-inputs.json')
            self.assertTrue(packets)
            self.assertEqual({s['chat_id'] for s in packets},{auto.lab.digest('dev-chat')})
            self.assertTrue(all(s['split']=='dev' for s in packets))

    def test_generation_context_freezes_prompt_and_disallows_eval_examples(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);packets,_,analysis=fixture(run)
            context={'instructions':'版本一','development_examples':[packets[0]]}
            analysis['generation_context_sha256']=auto.sha(context)
            auto.lab.write_json(run/'generation-context.json',context)
            auto.lab.write_json(run/'ai-analysis.json',analysis)
            auto.assemble(run)
            context['instructions']='事后修改';auto.lab.write_json(run/'generation-context.json',context)
            with self.assertRaisesRegex(ValueError,'版本'):auto.render(run)
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);packets,_,analysis=fixture(run)
            context={'development_examples':[{**packets[0],'chat_id':packets[1]['chat_id']}]}
            analysis['generation_context_sha256']=auto.sha(context)
            auto.lab.write_json(run/'generation-context.json',context)
            auto.lab.write_json(run/'ai-analysis.json',analysis)
            with self.assertRaisesRegex(ValueError,'交叉'):auto.assemble(run)

    def test_request_uses_frozen_extra_development_examples(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);packets,_,analysis=fixture(run)
            extra={**packets[0],'id':'life-dev','chat_id':'new-chat',
                   'context':[{'role':'对方','text':'停车位弄好了没'}], 'reference':['好了']}
            context={'development_examples':[packets[0],extra]}
            analysis['generation_context_sha256']=auto.sha(context)
            auto.lab.write_json(run/'generation-context.json',context)
            auto.lab.write_json(run/'ai-analysis.json',analysis)
            auto.assemble(run);auto.build_request(run,'停车位搞定了吗',run/'request-life.json')
            request=auto.lab.read_json(run/'request-life.json')
            self.assertIn('life-dev',request['provenance']['example_ids'])
            self.assertNotIn('dev',request['provenance']['example_ids'])
            self.assertNotIn('隐藏答案',str(request))

    def test_response_action_rating_is_independent_and_must_be_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);fixture(run);auto.assemble(run)
            manifest,_,_,comparison=auto.frozen_run(run)
            assessment={'comparison_sha256':auto.sha(comparison),'reviewer_kind':'ai','reviewer':'测试',
                        'items':[{'id':'eval','style':'贴近','meaning':'不同','action_alignment':'不同',
                                  'information_gap':'个人事实','unsupported_fact':False,'extra_commitment':False,
                                  'verdict':'短句不等于意思一样','reason':'检验维度分离'}]}
            report=auto.make_report(manifest,comparison,assessment)
            self.assertEqual(report['style'],{'贴近':1})
            self.assertEqual(report['action_alignment'],{'不同':1})
            del assessment['items'][0]['information_gap']
            with self.assertRaisesRegex(ValueError,'完整覆盖'):auto.make_report(manifest,comparison,assessment)

    def test_schedule_pressure_requires_own_words(self):
        sample={'context':[{'role':'对方','text':'有点赶'}]}
        self.assertEqual(auto.lab.suggest_context_labels(sample)['reply_state'],'待判断')
        sample['context'].append({'role':'我','text':'这个有点赶'})
        self.assertEqual(auto.lab.suggest_context_labels(sample)['reply_state'],'排期紧张')

    def test_interrupted_generation_cannot_overwrite_revealed_answers(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);fixture(run);write=auto.lab.write_json
            def interrupted(path,value):
                write(path,value)
                if path.name=='comparison.private.json':
                    raise OSError('模拟写出答案后中断')
            with patch.object(auto.lab,'write_json',side_effect=interrupted):
                with self.assertRaises(OSError):auto.assemble(run)
            self.assertFalse((run/'generation-manifest.json').exists())
            revealed=(run/'comparison.private.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'冻结'):auto.assemble(run)
            self.assertEqual((run/'comparison.private.json').read_bytes(),revealed)

    def test_learning_answers_and_identity_flags_must_match_source(self):
        for field in ('reference','identity_verified'):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as folder:
                run=Path(folder);packets,source,analysis=fixture(run)
                if field=='reference':source[0][field]=['不同学习答案']
                else:source[0][field]='False'
                auto.lab.write_json(run/'source.private.json',source)
                auto.lab.write_json(run/'manifest.json',{'input_sha256':auto.sha(packets),'source_sha256':auto.sha(source)})
                with self.assertRaises(ValueError):auto.assemble(run)

    def test_history_excludes_every_prior_batch_and_preserves_splits(self):
        with tempfile.TemporaryDirectory() as folder:
            history=Path(folder)
            for directory,name,sample in (
                ('manual','candidates.json',{'chat_id':'a','date':'2026-03-01','source':[row('me','',1)]}),
                ('first','source.private.json',{'chat_id':'b','date':'2026-03-02','split':'eval','source':[row('me','',2)]}),
                ('second','source.private.json',{'chat_id':'c','date':'2026-03-03','split':'dev','source':[row('me','',3)]})):
                (history/directory).mkdir()
                auto.lab.write_json(history/directory/name,[sample])
            days,sources,splits=auto.used_history(history)
            self.assertEqual(len(days),3)
            self.assertEqual(sources,{auto.source_key(row('me','',i)) for i in (1,2,3)})
            self.assertEqual(splits,{'b':'eval','c':'dev'})
            auto.lab.write_json(history/'second/source.private.json',[
                {'chat_id':'b','date':'2026-03-04','split':'dev'}])
            with self.assertRaisesRegex(ValueError,'冲突'):
                auto.used_history(history)

    def test_unknown_text_is_not_attributed_to_any_speaker(self):
        messages=[row('','身份未知的真实文字',1),row('other','问题',2),row('me','回复',3)]
        sample=auto.lab.make_candidates(messages,'me',min_reply_chars=1)[0]
        expanded=auto.expand_context(sample,messages,'me')
        self.assertNotIn('身份未知的真实文字',str(expanded['context']))
        self.assertEqual(expanded['context'][0]['role'],'未知')

    def test_render_checks_frozen_files_even_before_any_evaluation(self):
        for name in ('comparison.private.json','analysis-inputs.json','predictions.json'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as folder:
                run=Path(folder);fixture(run);auto.assemble(run)
                data=auto.lab.read_json(run/name)
                data[0]['unexpected_change']=True
                auto.lab.write_json(run/name,data)
                with self.assertRaisesRegex(ValueError,'冻结'):
                    auto.render(run)

    def test_render_recomputes_summary_and_verifies_evaluation_totals(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);fixture(run);auto.assemble(run)
            summary=auto.lab.read_json(run/'summary.json');summary['candidates']=999
            auto.lab.write_json(run/'summary.json',summary)
            auto.render(run)
            self.assertNotIn('999',(run/'results.html').read_text(encoding='utf-8'))
            assessment={'comparison_sha256':auto.sha(auto.lab.read_json(run/'comparison.private.json')),
                        'reviewer_kind':'ai','reviewer':'测试执行器','items':[
                            {'id':'eval','style':'贴近','meaning':'不同','unsupported_fact':False,
                             'extra_commitment':False,'verdict':'测试','reason':'测试'}]}
            auto.lab.write_json(run/'ai-evaluation.json',assessment);auto.evaluate(run)
            self.assertEqual(auto.lab.read_json(run/'summary.json')['candidates'],2)
            report=auto.lab.read_json(run/'evaluation-report.json');report['style']['贴近']=999
            auto.lab.write_json(run/'evaluation-report.json',report)
            with self.assertRaisesRegex(ValueError,'汇总'):
                auto.render(run)

    def test_mixed_keyword_hint_does_not_discard_work_examples(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);fixture(run);auto.assemble(run)
            auto.build_request(run,'下班看看接口字段',run/'mixed.json')
            request=auto.lab.read_json(run/'mixed.json')
            self.assertEqual(request['scene_hint']['scene'],'混合场景')
            self.assertEqual(request['provenance']['example_ids'],['dev'])

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
