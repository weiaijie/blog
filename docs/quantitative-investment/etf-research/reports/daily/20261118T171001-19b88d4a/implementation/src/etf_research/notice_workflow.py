"""Evidence-bound review records. No function changes an admission baseline."""
from datetime import date, datetime, timezone
from pathlib import Path
import hashlib, uuid
from .catalog_changes import canonical
from .notice_review import prepare_review
from .publication import read, sha, create, seal, verify_bundle, inside
from .http_capture import fetch, load_policy, save_transport

def write_packet(root, snapshot, output, download=False):
    root, output = Path(root), Path(output)
    packet = prepare_review(root / 'data/snapshots', snapshot)
    output.mkdir(parents=True, exist_ok=False)
    create(output / 'packet.json', packet)
    requests = []
    if download and packet['changes']:
        policy = load_policy(root / 'config/collection.json'); save_transport(output, policy)
        for change in packet['changes']:
            row = fetch(output, 'notice_' + change['change_id'], change['official_url'], policy)
            row.update(change_id=change['change_id'], pdf_magic_valid=(output / (row['name'] + '.body')).read_bytes().startswith(b'%PDF-'))
            requests.append(row)
    create(output / 'evidence_requests.json', requests)
    if packet['changes']:
        create(output / 'decision_template.json', dict(packet_sha256=packet['packet_sha256'], reviews=[dict(change_id=c['change_id'],
               conclusion='pending', evidence=[], effective_dates=[], rationale='', full_text_checked=False) for c in packet['changes']]))
    lines=['# 公告变化审阅清单','','此文件不批准行情或事件入账。分类只是提示，必须读完整官方公告。撤下公告不等于取消已登记分红。','',f"候选快照：{packet['candidate_snapshot']}；状态：{packet['status']}；变化：{len(packet['changes'])}项。"]
    for item in packet['changes']:
        r=item['after'] or item['before'];lines+=['',f"## {item['symbol']} / {item['kind']} / {r['TITLE']}",f"- 官方链接：{item['official_url']}",f"- 变更指纹：{item['change_id']}",f"- 相关事项提示：{', '.join(item['risk_hints'])}",'- 审阅状态：待核对；不得仅凭标题自动更新分红或停复牌。']
    if not packet['changes']:lines+=['','本次取得的目录与基线相同；这不证明上游绝无遗漏，也不独立批准价格或前瞻收益。']
    (output / 'REVIEW.md').write_text('\n'.join(lines)+'\n', encoding='utf-8'); seal(output)
    return packet

def validate_decision(root, packet, decision):
    if decision.get('packet_sha256') != packet['packet_sha256']: raise ValueError('Decision belongs to a different packet')
    changes = {c['change_id']: c for c in packet['changes']}; reviews = decision.get('reviews', [])
    if not reviews or len({r['change_id'] for r in reviews}) != len(reviews): raise ValueError('Empty or duplicate review decisions')
    for r in reviews:
        if r['change_id'] not in changes: raise ValueError('Unknown change fingerprint')
        if r.get('conclusion') not in ('no_account_effect', 'requires_event_or_rule_update', 'unresolved'): raise ValueError('Unsupported review conclusion')
        if not r.get('rationale', '').strip(): raise ValueError('Review rationale required')
        if r['conclusion'] != 'unresolved' and (r.get('full_text_checked') is not True or not r.get('evidence')): raise ValueError('Resolved review requires full text and evidence')
        for e in r.get('evidence', []):
            if not e.get('locator', '').strip(): raise ValueError('Evidence page/paragraph locator required')
            if sha(inside(root, e['path'])) != e['sha256']: raise ValueError('Review evidence changed')
        for d in r.get('effective_dates', []): date.fromisoformat(d)
    return reviews

def validate_packet(root, packet):
    raw = {k:v for k,v in packet.items() if k != 'packet_sha256'}
    if hashlib.sha256(canonical(raw).encode()).hexdigest() != packet['packet_sha256']: raise ValueError('Packet fingerprint mismatch')
    if prepare_review(Path(root) / 'data/snapshots', packet['candidate_snapshot'], packet['baseline_snapshot']) != packet: raise ValueError('Packet source evidence differs')

def save_decision(root, packet_folder, decision):
    root = Path(root); folder = inside(root, packet_folder); verify_bundle(folder)
    packet = read(folder / 'packet.json'); validate_packet(root, packet); validate_decision(root, packet, decision)
    output = root / 'reports/notice-decisions' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    record = dict(schema_version=1, recorded_at_utc=datetime.now(timezone.utc).isoformat(), packet_folder=folder.relative_to(root).as_posix(),
                  packet_file_sha256=sha(folder / 'packet.json'), decision=decision, approves_prices_or_events=False)
    create(output / 'decision.json', record); seal(output)
    return record

def review_queue(root):
    root = Path(root); decisions = {}
    records = []
    for path in (root / 'reports/notice-decisions').glob('*/decision.json'):
        verify_bundle(path.parent); record=read(path)
        stamp=datetime.fromisoformat(record['recorded_at_utc'])
        if stamp.tzinfo is None: raise ValueError('Review timestamp requires timezone')
        records.append((stamp, path.as_posix(), record))
    for _, _, record in sorted(records):
        folder = inside(root, record['packet_folder']); verify_bundle(folder)
        if sha(folder / 'packet.json') != record['packet_file_sha256']: raise ValueError('Reviewed packet changed')
        packet = read(folder / 'packet.json'); validate_packet(root, packet); validate_decision(root, packet, record['decision'])
        for r in record['decision']['reviews']: decisions[(packet['packet_sha256'], r['change_id'])] = r['conclusion']
    paths = list((root / 'reports/notice-reviews').glob('*/packet.json')) + list((root / 'reports/daily').glob('*/notice_review/packet.json'))
    queue = []
    for path in sorted(paths):
        verify_bundle(path.parent); packet = read(path); validate_packet(root, packet)
        if not packet['changes']: continue
        pending = sum(decisions.get((packet['packet_sha256'], c['change_id']), 'unresolved') == 'unresolved' for c in packet['changes'])
        queue.append(dict(packet_folder=path.parent.relative_to(root).as_posix(), packet_sha256=packet['packet_sha256'], changes=len(packet['changes']), pending_changes=pending, admission_still_blocked=True))
    return queue
