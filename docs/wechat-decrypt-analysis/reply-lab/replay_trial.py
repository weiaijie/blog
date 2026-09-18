"""Prepare dated historical inputs; generate before exposing reference answers."""
import argparse
import collections
import datetime as dt
import html
import json
from pathlib import Path

import auto_lab as auto
import reply_engine as engine
import reply_lab as lab
from codex_provider import generate,ProviderError

HERE=Path(__file__).resolve().parent
STYLE=HERE/'private/review-20260917-next-sample-check'


def prepare(out,batches):
    if out.exists() and any(out.iterdir()):raise ValueError('使用新目录，保留旧结果')
    samples=[]
    batch_hashes={}
    for batch in batches:
        manifest=lab.read_json(batch/'manifest.json')
        packets=lab.read_json(batch/'analysis-inputs.json')
        source=lab.read_json(batch/'source.private.json')
        if auto.sha(packets)!=manifest['input_sha256'] or auto.sha(source)!=manifest['source_sha256']:
            raise ValueError('抽样来源发生变化')
        samples.extend(s for s in source if s['split']=='eval')
        batch_hashes[batch.name]=auto.sha(manifest)
    if len({s['id'] for s in samples})!=len(samples):raise ValueError('评测样本重复')
    snapshot=lab.read_json(STYLE/'generation-context.json')
    if {s['chat_id'] for s in samples}&{s['chat_id'] for s in snapshot['development_examples']}:
        raise ValueError('开发与评测会话交叉')
    needed={auto.source_key(r) for s in samples for r in s['source']}
    rows={};chats={s['chat_id'] for s in samples};chat_rows={c:[] for c in chats};aliases=set()
    # One streaming read of the existing export; never reads decrypted keys.
    for row in lab.rows(lab.BASE/'analysis_output/all_messages_cleaned.csv'):
        chat=lab.digest(row['chat_username'])
        if chat in chats:
            chat_rows[chat].append(row)
            aliases.update(row[k] for k in ('chat_name','remark','nick_name','alias','sender_label','sender_username'))
            if auto.source_key(row) in needed:rows[auto.source_key(row)]=row
    aliases.discard('我');aliases.discard('me')
    inputs=[];references=[]
    for s in samples:
        target_source=s['source'][-len(s['reference'])]
        target=rows[auto.source_key(target_source)]
        cutoff=int(target['create_time']);self_id=target['sender_username']
        def convert(row):
            text=row['clean_text'] if row['message_kind']=='text' else '[缺失'+row['message_kind']+'内容]'
            return {'role':'我' if row['sender_username']==self_id else '对方' if row['sender_username'] else '未知',
                    'text':auto.mask(text,aliases),
                    'at':dt.datetime.fromtimestamp(int(row['create_time']),engine.TZ).isoformat(),
                    'source':{'db_file':row['db_file'],'table_name':row['table_name'],'local_id':row['local_id']}}
        current_rows=[rows[auto.source_key(r)] for r in s['source'][:-len(s['reference'])]
                      if int(rows[auto.source_key(r)]['create_time'])<cutoff]
        current=[convert(row) for row in current_rows]
        if not current:raise ValueError('目标之前无有效前文')
        query=auto.tokens(' '.join(m['text'] for m in current[-4:]))
        current_ids={auto.source_key(r) for r in current_rows}
        candidates=[]
        for row in chat_rows[s['chat_id']]:
            age=cutoff-int(row['create_time'])
            if (not 1800<age<=7*86400 or auto.source_key(row) in current_ids or row['message_kind']!='text'
                    or not row['sender_username'] or not 0<len(row['clean_text'])<=300):continue
            score=len(query&auto.tokens(row['clean_text']))
            if score>=2 and '[含凭据信息' not in auto.mask(row['clean_text'],aliases):
                candidates.append((score,int(row['create_time']),row))
        candidates.sort(key=lambda x:(-x[0],-x[1]))
        earlier=sorted([r for _,_,r in candidates[:6]],key=lambda r:int(r['create_time']))
        check={'source':[{k:r[k] for k in ('db_file','table_name','local_id','sender_username')} for r in earlier]}
        if not lab.verify_identity(check,lab.ROOT/'wechat-decrypt/decrypted/message'):raise ValueError('较早资料身份不符')
        inputs.append({'id':s['id'],'chat_id':s['chat_id'],'title':'历史片段 '+str(len(inputs)+1)+' / '+s['date'],
                       'as_of':dt.datetime.fromtimestamp(cutoff,engine.TZ).isoformat(),
                       'messages':current,'history':[convert(r) for r in earlier]})
        references.append({'id':s['id'],'reference':s['reference']})
    out.mkdir(parents=True,exist_ok=True)
    lab.write_json(out/'inputs.json',inputs)
    lab.write_json(out/'references.private.json',references)
    lab.write_json(out/'manifest.json',{'inputs_sha256':auto.sha(inputs),'references_sha256':auto.sha(references),
                   'batch_hashes':batch_hashes,'count':len(inputs),'development_shared_chats':0,
                   'earlier_messages':sum(len(s['history']) for s in inputs),
                   'source_latest':'2026-03-14','generator':'independent ephemeral CLI calls; default model',
                   'reviewer':'current Codex conversation; not human acceptance'})
    print(json.dumps({'prepared':len(inputs),'earlier_messages':sum(len(s['history']) for s in inputs)},ensure_ascii=False))


def run_trial(out):
    inputs=lab.read_json(out/'inputs.json');manifest=lab.read_json(out/'manifest.json')
    if auto.sha(inputs)!=manifest['inputs_sha256']:raise ValueError('输入改变')
    if any((out/name).exists() for name in ('requests.json','attempts.json','frozen.json','comparison.private.json')):
        raise ValueError('本轮已开始，不能重写；保留失败并使用新目录')
    requests=[{'id':s['id'],'request':engine.prepare_request(STYLE,s['messages'],as_of=s['as_of'],history=s['history'])} for s in inputs]
    # Store exact prompts before any generation or reference revelation.
    for s in requests:s['prompt']=engine.prompt_for(s['request'])
    lab.write_json(out/'requests.json',requests)
    lab.write_json(out/'started.json',{'requests_sha256':auto.sha(requests),'schema':engine.RESULT_SCHEMA,
                                    'inputs_sha256':manifest['inputs_sha256']})
    attempts=[]
    for index,s in enumerate(requests,1):
        try:
            result,execution=generate(s['prompt'],engine.RESULT_SCHEMA)
            engine.validate_result(result,s['request'])
            attempt={'id':s['id'],'result':result,'execution':execution,'status':'ok'}
        except ProviderError as exc:attempt={'id':s['id'],'status':'failed','error':str(exc)}
        attempts.append(attempt);lab.write_json(out/'attempts.json',attempts)
        print(json.dumps({'completed':index,'total':len(requests),'status':attempt['status']},ensure_ascii=False),flush=True)
    lab.write_json(out/'frozen.json',{'requests_sha256':auto.sha(requests),'attempts_sha256':auto.sha(attempts),
                                    'manifest_sha256':auto.sha(manifest),'started_sha256':auto.sha(lab.read_json(out/'started.json'))})


def reveal(out):
    frozen=lab.read_json(out/'frozen.json');requests=lab.read_json(out/'requests.json')
    attempts=lab.read_json(out/'attempts.json');manifest=lab.read_json(out/'manifest.json')
    refs=lab.read_json(out/'references.private.json')
    if (auto.sha(requests)!=frozen['requests_sha256'] or auto.sha(attempts)!=frozen['attempts_sha256']
            or auto.sha(manifest)!=frozen['manifest_sha256'] or auto.sha(refs)!=manifest['references_sha256']
            or auto.sha(lab.read_json(out/'inputs.json'))!=manifest['inputs_sha256']
            or auto.sha(lab.read_json(out/'started.json'))!=frozen['started_sha256']
            or len(attempts)!=len(refs) or {s['id'] for s in attempts}!={s['id'] for s in refs}):
        raise ValueError('冻结结果或评测清单发生变化')
    references={s['id']:s['reference'] for s in refs};req={s['id']:s['request'] for s in requests}
    comparison=[{**s,'request':req[s['id']],'reference':references[s['id']]} for s in attempts]
    lab.write_json(out/'comparison.private.json',comparison)
    return comparison


def assessment_report(comparison,assessments):
    if assessments and (assessments['comparison_sha256']!=auto.sha(comparison)
                         or {s['id'] for s in assessments['items']}!={s['id'] for s in comparison}
                         or len(assessments['items'])!=len(comparison)):
        raise ValueError('评价未覆盖本轮冻结结果')
    if not assessments:return None
    for s in assessments['items']:
        if (s.get('style') not in ('贴近','偏长','不贴近','无草稿')
                or s.get('action_alignment') not in ('一致','不同','无法复现')
                or s.get('meaning') not in ('一致','可兼容','不同','无法判断')
                or s.get('input_sufficiency') not in ('足够','不足')
                or type(s.get('unsupported_fact')) is not bool
                or type(s.get('extra_commitment')) is not bool or not s.get('reason')):
            raise ValueError('评价字段不完整')
    return {'count':len(comparison),'generation_success':sum(s['status']=='ok' for s in comparison),
            'with_draft':sum(bool(s.get('result',{}).get('draft')) for s in comparison),
            'scenes':dict(collections.Counter(s.get('result',{}).get('scene','失败') for s in comparison)),
            **{key:dict(collections.Counter(s[key] for s in assessments['items']))
               for key in ('style','action_alignment','meaning','input_sufficiency')},
            'unsupported_facts':sum(s['unsupported_fact'] for s in assessments['items']),
            'extra_commitments':sum(s['extra_commitment'] for s in assessments['items']),
            'comparison_sha256':auto.sha(comparison),'assessment_sha256':auto.sha(assessments),
            'reviewer':'当前会话 AI 复核，非本人验收'}


def render(out):
    comparison=reveal(out)
    assessments=lab.read_json(out/'assessment.json') if (out/'assessment.json').exists() else None
    report=assessment_report(comparison,assessments)
    ratings={s['id']:s for s in assessments['items']} if assessments else {}
    esc=html.escape
    chunks=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新回复回放</title>',
            '<style>body{font:16px/1.7 system-ui;max-width:960px;padding:20px;margin:auto;background:#eef2f6;color:#233544}article{background:white;padding:22px;margin:20px 0;border-radius:10px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}@media(max-width:600px){.pair{display:block}body{padding:12px}}small{color:#536779}</style>',
            '<h1>新样本回复回放</h1><p>生成由独立临时 Codex CLI 调用完成，先冻结再揭示历史答案；当前会话复核，不是本人评分。历史事实只用于当时回放。</p>']
    if report:
        lab.write_json(out/'evaluation-report.json',report)
        chunks.append('<p>'+str(report['count'])+' 条：'+str(report['with_draft'])+' 条有草稿。口吻：'+
                      esc(' / '.join(k+' '+str(v) for k,v in report['style'].items()))+'。回应动作：'+
                      esc(' / '.join(k+' '+str(v) for k,v in report['action_alignment'].items()))+
                      '。发现额外承诺 '+str(report['extra_commitments'])+' 条。以上是逐条复核统计。</p>')
    for s in comparison:
        r=s.get('result',{})
        chunks.append('<article><h2>'+esc(r.get('scene','生成失败')+' / '+r.get('response_action',''))+'</h2>')
        chunks.append('<details><summary>回复之前的资料</summary><pre>'+esc('\n'.join(e['id']+' '+e['role']+' ['+e['scope']+'] '+e['text'] for e in s['request']['evidence']))+'</pre></details>')
        chunks.append('<div class="pair"><div><h3>生成草稿</h3><pre>'+esc('\n'.join(r.get('draft',[])) or s.get('error','需要本人决定'))+'</pre></div><div><h3>历史回复</h3><pre>'+esc('\n'.join(s['reference']))+'</pre></div></div>')
        chunks.append('<small>'+esc(r.get('rationale',''))+'</small>')
        if s['id'] in ratings:chunks.append('<p>'+esc(ratings[s['id']]['reason'])+'</p>')
        chunks.append('</article>')
    (out/'results.html').write_text('\n'.join(chunks),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','render'])
    p.add_argument('--out',type=Path,required=True);p.add_argument('--batches',nargs='*',type=Path)
    args=p.parse_args()
    if args.command=='prepare':prepare(args.out,args.batches)
    elif args.command=='run':run_trial(args.out)
    else:render(args.out)
