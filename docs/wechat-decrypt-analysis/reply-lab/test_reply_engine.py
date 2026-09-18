import copy
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError

import app
import codex_provider as provider
import reply_engine as engine
import auto_lab as auto
import replay_trial
from test_auto_lab import fixture


def answer():
    return {'scene':'工作','reply_state':'待判断','response_action':'澄清','draft':['哪个字段'],
            'evidence_ids':['C1'],'state_evidence_ids':[], 'missing_facts':[],
            'rationale':'问具体字段','needs_confirmation':False}


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.run=Path(self.temp.name)
        fixture(self.run);auto.assemble(self.run)

    def tearDown(self):self.temp.cleanup()

    def prepare(self,messages=None,history=()):
        return engine.prepare_request(self.run,messages or [{'role':'对方','text':'哪个字段错了'}],
                                      as_of='2026-09-18T10:00:00+08:00',history=history)

    def test_sources_separate_future_expired_unknown_and_historical(self):
        request=self.prepare(history=[
            {'role':'我','text':'未来答案','at':'2026-09-18T11:00:00+08:00'},
            {'role':'我','text':'旧进度','at':'2026-08-01T10:00:00+08:00'},
            {'role':'未知','text':'不知谁说的','at':'2026-09-18T09:00:00+08:00'},
            {'role':'我','text':'昨天说已完成','at':'2026-09-17T10:00:00+08:00'},
            {'role':'我','text':'没有时间'}])
        self.assertEqual([s['id'] for s in request['evidence']],['C1','H4'])
        self.assertFalse(request['evidence'][1]['current_state_allowed'])
        self.assertEqual(len(request['excluded']),4)
        self.assertNotIn('未来答案',engine.prompt_for(request))
        self.assertNotIn('隐藏答案',engine.prompt_for(request))

    def test_unknown_only_or_future_only_rejected(self):
        for msg in [{'role':'未知','text':'某人说过'},
                    {'role':'对方','text':'未来消息','at':'2026-09-19T00:00:00+08:00'}]:
            with self.assertRaisesRegex(ValueError,'当前对话'):self.prepare([msg])

    def test_current_state_cannot_use_other_person_old_or_history(self):
        request=self.prepare([{'role':'对方','text':'我很忙'},
                              {'role':'我','text':'我很忙','at':'2026-09-18T08:00:00+08:00'},
                              {'role':'我','text':'[缺失image内容]'}])
        for identifier in ('C1','C2','C3','nonexistent'):
            result=answer();result.update(reply_state='暂时没空',state_evidence_ids=[identifier])
            with self.assertRaisesRegex(provider.ProviderError,'本人依据'):engine.validate_result(result,request)

    def test_dated_old_current_message_becomes_historical(self):
        request=self.prepare([{'role':'我','text':'当时完成了','at':'2026-09-17T10:00:00+08:00'},
                              {'role':'对方','text':'现在什么情况'}])
        self.assertEqual(request['evidence'][0]['scope'],'historical')
        self.assertFalse(request['evidence'][0]['current_state_allowed'])

    def test_recent_own_state_supported_and_no_missing_data_guess(self):
        request=self.prepare([{'role':'我','text':'我有点赶'},{'role':'对方','text':'今晚能做完吗'}])
        result=answer();result.update(reply_state='排期紧张',state_evidence_ids=['C1'])
        engine.validate_result(result,request)
        result.update(draft=[],missing_facts=[],needs_confirmation=False)
        with self.assertRaises(provider.ProviderError):engine.validate_result(result,request)
        result.update(missing_facts=['剩余工作量'],needs_confirmation=True)
        engine.validate_result(result,request)

    def test_invalid_citation_empty_list_and_schema_rejected(self):
        request=self.prepare()
        for change in ({'evidence_ids':['EXAMPLE1']},{'evidence_ids':[]},{'draft':'伪造'}, {'extra':'x'}):
            value=answer();value.update(change)
            with self.assertRaises(provider.ProviderError):engine.validate_result(value,request)

    def test_naive_dates_and_credentials_rejected(self):
        with self.assertRaisesRegex(ValueError,'时区'):
            self.prepare([{'role':'我','text':'忙','at':'2026-09-18T09:00:00'}])
        with self.assertRaisesRegex(ValueError,'凭据'):
            self.prepare([{'role':'对方','text':'密码: demo-not-a-real-secret'}])

    def test_parser_only_uses_explicit_roles(self):
        self.assertEqual([s['role'] for s in engine.parse_chat('我：好了\n对方：真的啊\n他说我很忙\n未知：不知道')],
                         ['我','对方','未知'])
        messages=engine.parse_chat('我：已经改好\n也测过了\n对方：可以上线吗')
        self.assertEqual(messages[0]['text'],'已经改好\n也测过了')

    def test_provider_timeout_and_failure_do_not_echo_private_output(self):
        with patch.object(provider.shutil,'which',return_value='codex'),patch.object(provider.subprocess,'run',side_effect=subprocess.TimeoutExpired('codex',1)):
            with self.assertRaisesRegex(provider.ProviderError,'超时'):provider.generate('private',{})
        with patch.object(provider.shutil,'which',return_value='codex'),patch.object(provider.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','secret stderr')):
            with self.assertRaises(provider.ProviderError) as caught:provider.generate('private',{})
            self.assertNotIn('secret',str(caught.exception))

    def test_provider_tool_attempt_rejected(self):
        events=json.dumps({'item':{'type':'command_execution'}})
        with patch.object(provider.shutil,'which',return_value='codex'),patch.object(provider.subprocess,'run',return_value=subprocess.CompletedProcess([],0,events,'')):
            with self.assertRaisesRegex(provider.ProviderError,'操作'):provider.generate('private',{})

    def test_http_real_routes_origin_and_no_private_files(self):
        def mock_provider(prompt,schema):return answer(),{'provider':'test','network_called':False}
        server=app.ReplyServer(('127.0.0.1',0),self.run,mock_provider)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            with urlopen(base) as response:
                self.assertIn(server.token,response.read().decode())
            for path in ('/private/source.private.json','/../auto_lab.py'):
                with self.assertRaises(HTTPError) as caught:urlopen(base+path)
                self.assertEqual(caught.exception.code,404)
            body=json.dumps({'text':'哪个字段错了'}).encode()
            headers={'Content-Type':'application/json','Origin':base,'X-Reply-Token':server.token}
            with urlopen(Request(base+'/api/reply',body,headers)) as response:
                value=json.load(response);self.assertEqual(value['result']['draft'],['哪个字段'])
            with patch.object(app,'HERE',self.run):
                payload=json.dumps({'id':value['id'],'edited':'哪个字段有问题'}).encode()
                with urlopen(Request(base+'/api/feedback',payload,headers)) as response:
                    self.assertTrue(json.load(response)['saved'])
                self.assertEqual(len(list((self.run/'private/feedback').glob('*.json'))),1)
            headers['Origin']='https://example.invalid'
            with self.assertRaises(HTTPError) as caught:urlopen(Request(base+'/api/reply',body,headers))
            self.assertEqual(caught.exception.code,403)
            self.assertEqual(len(server.responses),1)
        finally:server.shutdown();server.server_close();thread.join()

    def test_replay_source_change_fails_startup(self):
        replay=self.run/'inputs.json';auto.lab.write_json(replay,[{'id':'changed'}])
        with patch.object(app,'REPLAY',replay):
            with self.assertRaises((ValueError,KeyError)):app.ReplyServer(('127.0.0.1',0),self.run)

    def test_replay_freeze_rejects_tampering_and_incomplete_output(self):
        run=self.run/'replay';run.mkdir()
        inputs=[{'id':'a'}];refs=[{'id':'a','reference':['真正的答案']}]
        requests=[{'id':'a','request':{'evidence':[]},'prompt':'先生成'}]
        attempts=[{'id':'a','status':'ok','result':answer()}]
        manifest={'inputs_sha256':auto.sha(inputs),'references_sha256':auto.sha(refs)}
        started={'inputs_sha256':auto.sha(inputs)}
        values={'inputs.json':inputs,'references.private.json':refs,'requests.json':requests,
                'attempts.json':attempts,'manifest.json':manifest,'started.json':started}
        for name,value in values.items():auto.lab.write_json(run/name,value)
        frozen={'requests_sha256':auto.sha(requests),'attempts_sha256':auto.sha(attempts),
                'manifest_sha256':auto.sha(manifest),'started_sha256':auto.sha(started)}
        auto.lab.write_json(run/'frozen.json',frozen)
        self.assertEqual(replay_trial.reveal(run)[0]['reference'],['真正的答案'])
        attempts[0]['result']['draft']=['事后替换'];auto.lab.write_json(run/'attempts.json',attempts)
        with self.assertRaisesRegex(ValueError,'冻结'):replay_trial.reveal(run)
        with self.assertRaisesRegex(ValueError,'不能重写'):replay_trial.run_trial(run)

    def test_replay_summary_comes_from_ratings_not_written_claims(self):
        comparison=[{'id':'a','status':'ok','result':answer()}]
        rating={'id':'a','style':'偏长','action_alignment':'不同','meaning':'不同',
                'input_sufficiency':'不足','unsupported_fact':False,'extra_commitment':True,'reason':'多了承诺'}
        assessment={'comparison_sha256':auto.sha(comparison),'items':[rating],'summary':'虚假的全部正确'}
        report=replay_trial.assessment_report(comparison,assessment)
        self.assertEqual(report['extra_commitments'],1)
        self.assertEqual(report['style'],{'偏长':1})
        self.assertNotIn('虚假的',str(report))
        assessment['items']=[]
        with self.assertRaisesRegex(ValueError,'未覆盖'):replay_trial.assessment_report(comparison,assessment)

    def test_scene_eval_sampler_excludes_development_chat(self):
        from test_reply_lab import row
        source=[];own=[]
        for i,chat in enumerate(('dev-chat','eval-chat')):
            source.append({**row('other','到家吃饭了吗',10+i*10),'chat_username':chat})
            for offset in (1,2,3):
                sent={**row('me','到了',10+i*10+offset),'chat_username':chat};own.append(sent);source.append(sent)
        for s in source:s.update({k:'' for k in ('chat_name','remark','nick_name','alias','sender_label')})
        with patch.object(auto.lab,'HERE',self.run),patch.object(auto,'used_history',return_value=(set(),set(),{auto.lab.digest('dev-chat'):'dev'})), \
             patch.object(auto.lab,'rows',side_effect=lambda path:iter(own if path.name=='self_messages_cleaned.csv' else source)), \
             patch.object(auto.lab,'read_json',return_value={'db_dir':'C:/fake/me/db_storage'}), \
             patch.object(auto.lab,'verify_identity',return_value=True):
            auto.prepare(self.run/'scene-run',scene_evaluation=True)
        packets=auto.lab.read_json(self.run/'scene-run/analysis-inputs.json')
        self.assertTrue(packets);self.assertTrue(all(s['split']=='eval' for s in packets))
        self.assertNotIn(auto.lab.digest('dev-chat'),{s['chat_id'] for s in packets})


if __name__=='__main__':unittest.main()
