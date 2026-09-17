"""Automatic-data lane. Semantic analysis is supplied by the current AI session.

prepare -> AI reads analysis-inputs (eval answers hidden) -> assemble -> AI judges.
No API/network calls; no user-filled approvals, relationship labels or intent needed.
"""
import argparse
import collections
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re

import reply_lab as lab


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def mask(text, aliases):
    text = lab.redact(text, aliases)
    text = re.sub(r"@[\w\u4e00-\u9fffㅤ]+", "@[联系人]", text)
    text = re.sub(r"(?i)\b(?:[a-z0-9-]+\.)+(?:com|cn|net|org|io|club)\b", "[域名]", text)
    text = re.sub(r"分享人\s*[:：].*", "[分享元数据]", text)
    return text


def source_key(row):
    return tuple(str(row[k]) for k in ('db_file','table_name','local_id'))


def used_history(folder):
    """All prepared batches count as seen, even if they were never evaluated."""
    days, sources, splits = set(), set(), {}
    paths = sorted(set(folder.glob('*/source.private.json')) | set(folder.glob('*/candidates.json')))
    for path in paths:
        for sample in lab.read_json(path):
            days.add((sample['chat_id'], sample['date']))
            sources.update(source_key(row) for row in sample.get('source', []))
            split = sample.get('split')
            if split in ('dev','eval'):
                chat = sample['chat_id']
                if chat in splits and splits[chat] != split:
                    raise ValueError('历史会话的开发/评测划分冲突')
                splits[chat] = split
    return days, sources, splits


def expand_context(sample, messages, self_id):
    target = sample['source'][-len(sample['reference'])]
    ordered = sorted(messages, key=lambda r: (int(r['create_time']), int(r['local_id'])))
    index = next(i for i,r in enumerate(ordered) if all(r[k]==target[k] for k in ('db_file','table_name','local_id')))
    before=[]
    size=0
    for r in reversed(ordered[max(0,index-24):index]):
        if int(ordered[index]['create_time'])-int(r['create_time'])>1800:
            break
        text=r['clean_text'] if r['message_kind']=='text' else '[缺失'+r['message_kind']+'内容]'
        if not r['sender_username'] and r['message_kind']=='text':
            text='[未知发送者文本，未纳入上下文]'
        if size+len(text)>3500:
            break
        before.insert(0,(r,text))
        size+=len(text)
    peers={}
    sample['context']=[]
    for r,text in before:
        sender=r['sender_username']
        if sender and sender != self_id:
            peers.setdefault(sender,'对方'+str(len(peers)+1))
        sample['context'].append({'role':'我' if sender==self_id else '对方' if sender else '未知',
                                  'speaker':'我' if sender==self_id else peers[sender] if sender else '未知发送者',
                                  'text':text})
    sample['source']=[{k:r[k] for k in ('db_file','table_name','local_id','sender_username')} for r,t in before if r['sender_username']] + sample['source'][-len(sample['reference']):]
    return sample


def scene_seeds(text):
    """Retrieval cues only, never semantic labels or evaluation hints."""
    if any(word in text for word in ('接口','代码','客户','需求','上线','数据库','后台','前端','测试')):
        return []
    groups = {'情绪线索':('难过','委屈','伤心','心情','担心','害怕','心烦','失眠','烦死','不开心'),
              '闲聊线索':('哈哈','好玩','电影','游戏','笑死','搞笑','开玩笑'),
              '生活线索':('吃饭','外卖','到家','快递','睡觉','做饭','买菜','停车','散步')}
    return [name for name,words in groups.items() if any(word in text for word in words)]


def prepare(out, scene_development=False):
    if out.exists() and any(out.iterdir()):
        raise ValueError("使用新输出目录，保留此前结果")
    old_days, old_sources, old_splits = used_history(lab.HERE/'private')
    self_csv = lab.BASE / "analysis_output/self_messages_cleaned.csv"
    senders, activity, metadata = collections.Counter(), collections.Counter(), {}
    latest = 0
    for row in lab.rows(self_csv):
        senders[row['sender_username']] += 1
        latest = max(latest, int(row['create_time']))
    if len(senders) != 1 or not next(iter(senders)):
        raise ValueError("无法确定本人身份")
    self_id = next(iter(senders))
    account = Path(lab.read_json(lab.ROOT / 'wechat-decrypt/config.json')['db_dir']).parent.name
    if self_id not in (account, re.sub(r'_[0-9a-fA-F]{4,}$', '', account)):
        raise ValueError("本人身份与配置不一致")
    cutoff = latest - (365 if scene_development else 180) * 86400
    for row in lab.rows(self_csv):
        if int(row['create_time']) >= cutoff and row['message_kind'] == 'text' and row['chat_username'] != self_id:
            activity[row['chat_username']] += 1
            metadata[row['chat_username']] = row
    selected = []
    partitions = {}
    if scene_development:
        eligible = {chat for chat,n in activity.items() if n >= 3 and metadata[chat]['is_group']=='False'
                    and old_splits.get(lab.digest(chat)) != 'eval'}
        scores = collections.defaultdict(collections.Counter)
        for row in lab.rows(lab.BASE/'analysis_output/all_messages_cleaned.csv'):
            if (row['chat_username'] in eligible and int(row['create_time']) >= cutoff
                    and row['message_kind']=='text' and row['sender_username'] and row['sender_username'] != self_id):
                for seed in scene_seeds(row['clean_text']):
                    scores[seed][row['chat_username']] += 1
        for seed in ('情绪线索','闲聊线索','生活线索'):
            for chat,_ in scores[seed].most_common(3):
                if chat not in selected:
                    selected.append(chat)
                    partitions[chat] = 'dev'
    else:
        for group, n in (('False', 8), ('True', 4)):
            chats = [c for c, _ in activity.most_common() if metadata[c]['is_group'] == group][:n]
            for i, chat in enumerate(chats):
                selected.append(chat)
                partitions[chat] = old_splits.get(lab.digest(chat), 'dev' if i % 2 == 0 else 'eval')
    messages = {chat: [] for chat in selected}
    aliases = set()
    for row in lab.rows(lab.BASE / 'analysis_output/all_messages_cleaned.csv'):
        if row['chat_username'] in messages and int(row['create_time']) >= cutoff:
            messages[row['chat_username']].append(row)
            aliases.update(row[k] for k in ('chat_name', 'remark', 'nick_name', 'alias', 'sender_label', 'sender_username'))
    aliases.discard('me')
    aliases.discard('我')
    used, output, checks, seed_counts = set(), [], collections.Counter(), collections.Counter()
    for chat in selected:
        entries = lab.make_candidates(messages[chat], self_id, context_turns=12, context_chars=3500, min_reply_chars=1)
        days = set()
        for s in reversed(entries):
            if len(days) >= 4:
                break
            if s['date'] in days or (s['chat_id'], s['date']) in old_days:
                checks['seen_day_excluded'] += 1
                continue
            s=expand_context(s,messages[chat],self_id)
            if scene_development:
                seeds = scene_seeds(' '.join(m['text'] for m in s['context'][-8:]))
                seeds = [seed for seed in seeds if seed_counts[seed] < 8]
                if not seeds:
                    continue
                seed = min(seeds, key=lambda value:seed_counts[value])
            if any(source_key(row) in old_sources for row in s['source']):
                checks['seen_context_excluded'] += 1
                continue
            s['context'] = [{**m, 'text': mask(m['text'], aliases)} for m in s['context']]
            s['reference'] = [mask(t, aliases) for t in s['reference']]
            texts = [m['text'] for m in s['context']] + s['reference']
            if any('[含凭据信息' in t for t in texts):
                checks['credential_excluded'] += 1
                continue
            if not any(re.sub(r'\[[^\]]*\]|\s|@', '', t) for t in s['reference']):
                checks['nonverbal_excluded'] += 1
                continue
            fingerprint = sha([s['context'], s['reference']])
            if fingerprint in used:
                continue
            if not lab.verify_identity(s, lab.ROOT / 'wechat-decrypt/decrypted/message'):
                checks['identity_failed'] += 1
                continue
            s.update(identity_verified=True, split=partitions[chat])
            output.append(s)
            if scene_development:
                seed_counts[seed] += 1
            used.add(fingerprint)
            days.add(s['date'])
    # Partition before exposing examples to the AI. No answer/intent-derived labels in eval inputs.
    packets = []
    for s in output:
        p = {k: s[k] for k in ('id', 'chat_id', 'date', 'split', 'context')}
        p['channel'] = '群聊' if s['object_type'] == '群聊' else '私聊'
        if s['split'] == 'dev':
            p['reference'] = s['reference']
        packets.append(p)
    if not output:
        raise ValueError('没有未见过的可用候选；请扩大数据范围，不回退重复样本')
    out.mkdir(parents=True, exist_ok=True)
    lab.write_json(out / 'source.private.json', output)
    lab.write_json(out / 'analysis-inputs.json', packets)
    manifest = {'input_sha256': sha(packets), 'source_sha256': sha(output),
                'counts': dict(collections.Counter(s['split'] for s in output)),
                'source_latest': dt.datetime.fromtimestamp(latest).isoformat(),
                'context_messages_max': 24, 'context_window_seconds': 1800, 'context_chars_max': 3500,
                'sampling': {'mode':'scene_development' if scene_development else 'active_chats',
                             'days':365 if scene_development else 180, 'keyword_seed_counts':dict(seed_counts)},
                'identity_verified': len(output), 'filters': dict(checks),
                'history_exclusion': {'chat_days':len(old_days),'source_rows':len(old_sources),
                                      'preserved_chat_splits':len(old_splits)},
                'user_input_required': False, 'semantic_executor': 'current_conversation_ai',
                'privacy': '自动遮罩，语义复核在当前会话完成；不保证完全匿名',
                'evaluation_limit': '本会话此前看过其他历史样本，本轮目标答案未提供；不是独立模型盲测',
                'shared_chats': sorted({s['chat_id'] for s in output if s['split']=='dev'} & {s['chat_id'] for s in output if s['split']=='eval'})}
    lab.write_json(out / 'manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False))


def validate_analysis(packets, analysis):
    if len({s['id'] for s in packets}) != len(packets):
        raise ValueError('输入 ID 重复')
    if analysis.get('input_sha256') != sha(packets):
        raise ValueError('AI 结果与本批输入不匹配')
    if analysis.get('reviewer_kind') != 'ai' or not analysis.get('reviewer'):
        raise ValueError('必须声明 AI 审核来源')
    entries = analysis['items']
    if len({s['id'] for s in entries}) != len(entries) or {s['id'] for s in entries} != {s['id'] for s in packets}:
        raise ValueError('AI 分析必须覆盖完整清单且 ID 不重复')
    by_id = {s['id']: s for s in packets}
    for s in entries:
        if s['scene'] not in lab.SCENES or s['reply_state'] not in lab.STATES:
            raise ValueError('无效场景/状态')
        if s['quality'] not in ('usable', 'insufficient', 'excluded') or s['confidence'] not in ('high', 'medium', 'low'):
            raise ValueError('无效质量/置信度')
        if not s.get('reason') or not s.get('evidence_indices'):
            raise ValueError('缺少分析依据')
        if any(type(i) is not int or i < 1 or i > len(by_id[s['id']]['context']) for i in s['evidence_indices']):
            raise ValueError('上下文依据索引越界')
        state_evidence = s.get('state_evidence_indices', [])
        if s['reply_state'] != '待判断' and not state_evidence:
            raise ValueError('本人状态缺少本人前文依据')
        if any(type(i) is not int or i < 1 or i > len(by_id[s['id']]['context'])
               or by_id[s['id']]['context'][i-1]['role'] != '我' for i in state_evidence):
            raise ValueError('本人状态不能借用对方发言')
        if by_id[s['id']]['split'] == 'eval' and s['quality'] == 'usable':
            if not isinstance(s.get('draft'), list) or not s['draft'] or not all(isinstance(t,str) and t.strip() for t in s['draft']):
                raise ValueError('可用评测样本缺少生成回复')
    return entries


def check_generation_context(run, analysis):
    if 'generation_context_sha256' in analysis:
        context = lab.read_json(run/'generation-context.json')
        if sha(context) != analysis['generation_context_sha256']:
            raise ValueError('生成使用的提示或风格资料版本已改变')
        examples = context.get('development_examples', [])
        packets = lab.read_json(run/'analysis-inputs.json')
        evaluation = [s for s in packets if s['split']=='eval']
        if (len({s['id'] for s in examples}) != len(examples)
                or any(s.get('split') != 'dev' or not s.get('reference')
                       or s['id'] in {p['id'] for p in evaluation}
                       or s['chat_id'] in {p['chat_id'] for p in evaluation} for s in examples)):
            raise ValueError('风格资料中的示例不能与本轮评测交叉')
        return context
    return None


def assemble(run):
    if any((run/name).exists() for name in ('generation-manifest.json','predictions.json','comparison.private.json')):
        raise ValueError('本轮生成已冻结；请用新目录开展下一轮，或 render 查看已有结果')
    packets = lab.read_json(run/'analysis-inputs.json')
    analysis = lab.read_json(run/'ai-analysis.json')
    entries = validate_analysis(packets, analysis)
    check_generation_context(run, analysis)
    manifest = lab.read_json(run/'manifest.json')
    raw_source = lab.read_json(run/'source.private.json')
    if manifest['input_sha256'] != sha(packets) or manifest['source_sha256'] != sha(raw_source):
        raise ValueError('本批来源或输入被修改')
    source = {s['id']: s for s in raw_source}
    if len(source) != len(raw_source) or set(source) != {s['id'] for s in packets}:
        raise ValueError('来源清单不匹配')
    chats = {'dev': set(), 'eval': set()}
    for p in packets:
        s = source[p['id']]
        if p['split'] not in chats or s.get('identity_verified') is not True:
            raise ValueError('划分或身份核验缺失')
        if any(s[k] != p[k] for k in ('context','split','chat_id')):
            raise ValueError('来源与输入内容不一致')
        if p['split'] == 'eval' and 'reference' in p:
            raise ValueError('评测输入不得包含目标答案')
        if p['split'] == 'dev' and p.get('reference') != s['reference']:
            raise ValueError('学习答案与来源不一致')
        chats[p['split']].add(p['chat_id'])
    if chats['dev'] & chats['eval']:
        raise ValueError('同一会话不能跨开发和评测组')
    by_id = {s['id']: s for s in entries}
    dev, inputs, predictions, comparison = [], [], [], []
    for p in packets:
        a, s = by_id[p['id']], source[p['id']]
        if a['quality'] != 'usable':
            continue
        clean = {k:p[k] for k in ('id','context','channel')}
        clean.update(scene=a['scene'], reply_state=a['reply_state'], label_source='AI 基于回复前上下文')
        if p['split']=='dev':
            dev.append({**clean, 'reference':s['reference']})
        else:
            inputs.append(clean)
            predictions.append({'id':p['id'],'draft':a['draft'],'reviewer':analysis['reviewer']})
            comparison.append({**clean,'draft':a['draft'],'reference':s['reference']})
    lab.write_json(run/'dev.json', dev)
    lab.write_json(run/'eval-inputs.json', inputs)
    lab.write_json(run/'predictions.json', predictions)
    lab.write_json(run/'comparison.private.json', comparison)
    lab.write_json(run/'generation-manifest.json', {
        'analysis_sha256': sha(analysis), 'predictions_sha256': sha(predictions),
        'comparison_sha256': sha(comparison), 'input_sha256': sha(packets),
        'created_at': dt.datetime.now().isoformat(), 'eval_ids': [s['id'] for s in predictions]})
    summary = make_summary(packets, analysis)
    lab.write_json(run/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False))
    render(run)


def frozen_run(run):
    """Validate every consumer, including rendering before any ratings exist."""
    manifest = lab.read_json(run/'generation-manifest.json')
    packets = lab.read_json(run/'analysis-inputs.json')
    analysis = lab.read_json(run/'ai-analysis.json')
    comparisons = lab.read_json(run/'comparison.private.json')
    predictions = lab.read_json(run/'predictions.json')
    if (manifest['predictions_sha256'] != sha(predictions)
            or manifest['comparison_sha256'] != sha(comparisons)
            or manifest['analysis_sha256'] != sha(analysis)
            or manifest['input_sha256'] != sha(packets)):
        raise ValueError('生成结果或输入已改变，与冻结清单不匹配')
    validate_analysis(packets, analysis)
    check_generation_context(run, analysis)
    expected = {s['id'] for s in analysis['items'] if s['quality']=='usable'} & {
        p['id'] for p in packets if p['split']=='eval'}
    for values in (manifest['eval_ids'], [s['id'] for s in predictions], [s['id'] for s in comparisons]):
        if len(values) != len(expected) or set(values) != expected:
            raise ValueError('冻结的评测清单不匹配')
    return manifest, packets, analysis, comparisons


def make_summary(packets, analysis, evaluated=False):
    entries = analysis['items']
    usable = {s['id'] for s in entries if s['quality']=='usable'}
    return {'candidates':len(packets), 'quality':dict(collections.Counter(s['quality'] for s in entries)),
            'scenes':dict(collections.Counter(s['scene'] for s in entries)),
            'states':dict(collections.Counter(s['reply_state'] for s in entries)),
            'dev':sum(s['split']=='dev' and s['id'] in usable for s in packets),
            'eval_generated':sum(s['split']=='eval' and s['id'] in usable for s in packets),
            'human_ratings':0, 'analysis_source':analysis['reviewer'],
            'evaluation':'已完成本会话 AI 对照自评；不是本人评分' if evaluated else '待 AI 对照评估；不是本人评分'}


def make_report(manifest, comparisons, assessment):
    if assessment.get('comparison_sha256') != sha(comparisons):
        raise ValueError('评价与冻结的生成结果不匹配')
    if assessment.get('reviewer_kind') != 'ai' or not assessment.get('reviewer'):
        raise ValueError('评价必须声明 AI 来源')
    items = assessment['items']
    if len({s['id'] for s in items}) != len(items) or {s['id'] for s in items} != set(manifest['eval_ids']):
        raise ValueError('评价必须完整覆盖生成清单，不得删除难例')
    for s in items:
        if (s.get('style') not in ('贴近','偏长','不贴近')
                or s.get('meaning') not in ('一致','可兼容','不同','无法判断')
                or type(s.get('unsupported_fact')) is not bool
                or type(s.get('extra_commitment')) is not bool
                or not s.get('verdict') or not s.get('reason')):
            raise ValueError('评价字段不完整')
    action_review = any('action_alignment' in s or 'information_gap' in s for s in items)
    if action_review and any(s.get('action_alignment') not in ('一致','不同','无法判断')
                             or s.get('information_gap') not in ('无','当前任务进度','系统知识','个人事实','指代或媒体','隐含意图')
                             for s in items):
        raise ValueError('回应动作与信息缺口评价必须完整覆盖')
    by_id = {s['id']: s for s in items}
    grouped = {}
    for field in ('scene','reply_state'):
        grouped[field] = {}
        for label in sorted({s[field] for s in comparisons}):
            subset = [by_id[s['id']] for s in comparisons if s[field] == label]
            grouped[field][label] = {
                'count': len(subset), 'style': dict(collections.Counter(s['style'] for s in subset)),
                'meaning': dict(collections.Counter(s['meaning'] for s in subset))}
    report = {'reviewer': assessment['reviewer'], 'reviewer_kind': 'ai', 'human_ratings': 0,
              'evaluated': len(items), 'style': dict(collections.Counter(s['style'] for s in items)),
              'meaning': dict(collections.Counter(s['meaning'] for s in items)),
              'unsupported_facts': sum(s['unsupported_fact'] for s in items),
              'extra_commitments': sum(s['extra_commitment'] for s in items), 'groups': grouped,
              'evaluation_sha256': sha(assessment),
              'limits': '同一会话 AI 的历史对照自评；不代表本人评分、独立盲测或场景覆盖率。'}
    if action_review:
        report['action_alignment'] = dict(collections.Counter(s['action_alignment'] for s in items))
        report['information_gaps'] = dict(collections.Counter(s['information_gap'] for s in items))
    return report


def evaluate(run):
    manifest, packets, analysis, comparisons = frozen_run(run)
    report = make_report(manifest, comparisons, lab.read_json(run/'ai-evaluation.json'))
    lab.write_json(run/'evaluation-report.json', report)
    lab.write_json(run/'summary.json', make_summary(packets, analysis, evaluated=True))
    print(json.dumps(report, ensure_ascii=False))
    render(run)


def render(run):
    manifest, packets, raw_analysis, data = frozen_run(run)
    summary=make_summary(packets, raw_analysis)
    source_latest=lab.read_json(run/'manifest.json').get('source_latest','未记录最新日期')
    analysis={s['id']:s for s in raw_analysis['items']}
    assessments = {}
    report = None
    if (run/'evaluation-report.json').exists():
        assessment=lab.read_json(run/'ai-evaluation.json')
        report=make_report(manifest, data, assessment)
        if report != lab.read_json(run/'evaluation-report.json'):
            raise ValueError('评价或汇总已改变，请重新 evaluate')
        assessments={s['id']:s for s in assessment['items']}
    chunks=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>自动分析结果</title>',
            '<style>body{font:16px/1.7 system-ui;background:#f5f3ed;color:#25362c;max-width:950px;margin:auto;padding:24px}article{background:white;margin:20px 0;padding:24px;border-radius:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}h1{font-size:28px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}td,th{text-align:left;vertical-align:top;padding:6px;border-bottom:1px solid #ddd}table{width:100%;border-collapse:collapse;overflow-wrap:anywhere}@media(max-width:600px){.pair{display:block}body{padding:14px}article{padding:16px}}small{color:#58655a}</style>',
            '<h1>历史回复 · 自动分析结果</h1><p>已由 AI 补上下文、分类、筛选和生成。无需填写样本表；此页用于查看与可选纠错。原回复只在生成结果保存后揭示。</p>',
            '<p>本轮 '+str(summary['candidates'])+' 段：'+str(summary['dev'])+' 段用于学习，'+str(summary['eval_generated'])+' 段已生成对照。上下文不足的样本单列，不编造当时的事实。</p>',
            '<p>场景：'+html.escape(' / '.join(k+' '+str(v) for k,v in summary['scenes'].items()))+'</p>',
            '<p>本人状态：'+html.escape(' / '.join(k+' '+str(v) for k,v in summary['states'].items()))+'</p>',
            '<p><small>历史快照最新时间：'+html.escape(source_latest)+'。本轮按会话分组；同一会话 AI 分析、生成和对照，不是本人评分或独立盲测。“正常回应”仅描述已有中性文字，无法观察内心状态。</small></p>']
    if report:
        chunks += ['<p>AI 风格评价：'+html.escape(' / '.join(k+' '+str(v) for k,v in report['style'].items()))+
                   '。历史意思对照：'+html.escape(' / '.join(k+' '+str(v) for k,v in report['meaning'].items()))+'。</p>']
        if 'action_alignment' in report:
            chunks += ['<p>回应动作：'+html.escape(' / '.join(k+' '+str(v) for k,v in report['action_alignment'].items()))+
                       '。口吻贴近不等于选对回应动作；本轮与旧轮样本不同，不能直接比较准确率。</p>']
    if 'generation_context_sha256' in raw_analysis:
        context=lab.read_json(run/'generation-context.json')
        profile=context.get('style_profile',{})
        chunks += ['<details><summary>查看分场景说话方式与不同状态的区别</summary><p>以下规则由开发记录归纳；证据少的场景暂定，历史事实不能当成当前事实。</p>']
        for name,facet in profile.get('facets',{}).items():
            chunks += ['<h3>'+html.escape(name)+'</h3><small>'+html.escape(facet.get('support',''))+'</small><ul>']
            chunks += ['<li>'+html.escape(rule)+'</li>' for rule in facet.get('rules',[])]
            chunks += ['</ul>']
        for name,state in profile.get('states',{}).items():
            if isinstance(state,dict):
                chunks += ['<p><strong>'+html.escape(name)+'：</strong>'+html.escape(state['rule'])+'</p>']
        chunks += ['</details>']
    chunks += ['<details><summary>查看全部样本的分类依据与未生成原因</summary><table><thead><tr><th>场景 / 状态</th><th>用途</th><th>依据</th></tr></thead><tbody>']
    quality_names={'usable':'可用','insufficient':'上下文不足','excluded':'排除'}
    for p in packets:
        a=analysis[p['id']]
        chunks += ['<tr><td>'+html.escape(a['scene']+' / '+a['reply_state'])+'</td><td>'+html.escape(('学习' if p['split']=='dev' else '评测')+' · '+quality_names[a['quality']])+'</td><td>'+html.escape(a['reason'])+'</td></tr>']
    chunks += ['</tbody></table></details>']
    for s in data:
        a=analysis[s['id']]
        chunks += ['<article><h2>'+html.escape(s['scene']+' · '+s['reply_state'])+'</h2>',
                   '<small>'+html.escape(a['reason'])+'</small><details><summary>回复前上下文</summary><pre>'+html.escape('\n'.join(m.get('speaker',m['role'])+'：'+m['text'] for m in s['context']))+'</pre></details>',
                   '<div class="pair"><div><h3>AI 生成</h3><pre>'+html.escape('\n'.join(s['draft']))+'</pre></div><div><h3>历史真实回复</h3><pre>'+html.escape('\n'.join(s['reference']))+'</pre></div></div>']
        if s['id'] in assessments:
            e=assessments[s['id']]
            chunks += ['<p>AI 对照评价：'+html.escape(e['verdict']+'；'+e['reason'])+'</p>']
            if 'action_alignment' in e:
                chunks += ['<small>口吻 '+html.escape(e['style'])+' / 回应动作 '+html.escape(e['action_alignment'])+
                           ' / 信息缺口 '+html.escape(e['information_gap'])+'</small>']
        chunks += ['</article>']
    (run/'results.html').write_text('\n'.join(chunks),encoding='utf-8')


def tokens(text):
    result = set(re.findall(r'[a-z][a-z0-9_]*', text.lower()))
    for phrase in re.findall(r'[\u4e00-\u9fff]+', text):
        result.update(phrase[i:i+2] for i in range(max(1,len(phrase)-1)))
    return result - {'这个','那个','了吗','了没','一下','什么','怎么','现在','可以','已经',
                     '好的','没有','你们','我们','不是','到了','过了','完了','定了'}


def build_request(run, message, out):
    """Prepare a request for the AI executor, using development examples only."""
    if not message or not message.strip():
        raise ValueError('消息不能为空')
    if out.exists():
        raise ValueError('请求输出已存在，请使用新文件')
    message = mask(message, ())
    if '[含凭据信息' in message:
        raise ValueError('消息包含凭据信息，整条排除')
    dev = lab.read_json(run/'dev.json')
    packets = lab.read_json(run/'analysis-inputs.json')
    analysis = lab.read_json(run/'ai-analysis.json')
    validate_analysis(packets, analysis)
    snapshot = check_generation_context(run, analysis)
    manifest = lab.read_json(run/'generation-manifest.json')
    if manifest['input_sha256'] != sha(packets) or manifest['analysis_sha256'] != sha(analysis):
        raise ValueError('学习来源已改变')
    allowed = {p['id']:p for p in packets if p['split']=='dev'}
    labels = {s['id']:s for s in analysis['items']}
    if len({s['id'] for s in dev}) != len(dev) or any(s['id'] not in allowed for s in dev):
        raise ValueError('检索示例必须来自开发组')
    for s in dev:
        if s['context'] != allowed[s['id']]['context'] or s['reference'] != allowed[s['id']]['reference']:
            raise ValueError('学习示例已改变')
        if labels[s['id']]['quality'] != 'usable' or any(s[k] != labels[s['id']][k] for k in ('scene','reply_state')):
            raise ValueError('学习示例标签已改变或不可用')
    if snapshot and snapshot.get('development_examples'):
        own_examples = {s['id']:s for s in dev}
        dev = []
        for s in snapshot['development_examples']:
            hint = lab.suggest_context_labels(s)
            example = {k:s[k] for k in ('id','context','reference','channel')}
            example.update(scene=hint['scene'], reply_state=hint['reply_state'],
                           label_source='补充示例的规则检索建议，当前话题仍须语义判断')
            dev.append(own_examples.get(s['id'], example))
    hint = lab.suggest_context_labels({'context':[{'role':'对方','text':message}]})
    query = tokens(message)
    ranked = []
    for s in dev:
        words = tokens(' '.join(m['text'] for m in s['context'][-4:]))
        overlap = len(query & words) / max(1,len(query | words))
        # Keyword hints can be wrong or mixed; they must not eliminate useful examples.
        if hint['scene'] == s['scene'] and hint['scene'] != '待判断':
            overlap *= 1.25
        ranked.append((overlap, s['id'], s))
    ranked.sort(key=lambda v:(-v[0], v[1]))
    examples = [s for score,_,s in ranked[:3] if score > 0]
    prompt = (lab.HERE/'auto_prompt.txt').read_text(encoding='utf-8')
    profile_path = run/'style-profile.json'
    request = {'executor':'current_conversation_ai', 'network_called':False,
               'instructions':prompt, 'message':message, 'scene_hint':hint,
               'style_profile':lab.read_json(profile_path) if profile_path.exists() else None,
               'examples':examples, 'retrieval':'中文双字片段和英文词重合排序，场景建议仅加权；非语义向量检索',
               'provenance':{'generation_manifest_sha256':sha(manifest),
                             'generation_context_sha256':analysis.get('generation_context_sha256'),
                             'example_ids':[s['id'] for s in examples]},
               'output_schema':{'scene':'场景或待判断','reply_state':'状态或待判断',
                                'response_action':'承接/澄清/说明/推进/延后/无法确定',
                                'draft':['短消息'],'missing_facts':['缺少的当前事实']}}
    lab.write_json(out,request)
    print(json.dumps({'request':str(out),'examples':len(examples),'network_called':False},ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','prepare-scenes','assemble','evaluate','render','request'])
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--message')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.command == 'prepare-scenes':
        prepare(args.run, scene_development=True)
        return
    if args.command == 'request':
        if args.message is None or args.out is None:
            parser.error('request 需要 --message 和 --out')
        build_request(args.run,args.message,args.out)
        return
    {'prepare':prepare,'assemble':assemble,'evaluate':evaluate,'render':render}[args.command](args.run)


if __name__=='__main__':
    main()
