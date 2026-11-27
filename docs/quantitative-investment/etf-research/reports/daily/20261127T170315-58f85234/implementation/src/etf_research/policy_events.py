"""Read-only policy evidence and conservative point-in-time version selection."""
import argparse
from copy import deepcopy
from datetime import date, datetime, time, timedelta
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Asia/Shanghai')
SNAPSHOT = 'data/snapshots/20261127-policy-events-1600'
SNAPSHOT_SHA = '89f7cae39c2021eaed0d8c6b7bc7a6cecb98bca0bacf4789f832e75ca1f2e5ff'
SEED = 'reports/2026-11-27-policy-data-plan/event-examples.json'
SEED_SHA = '945d448a8e3d0761d754490c0609d82342b82668703ddb48455a8e761fb6f707'


def instant(value, *, local_zone=None):
    if not isinstance(value, str) or not re.fullmatch(
            r'\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d(?:\.\d{1,6})?)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)', value):
        raise ValueError('Explicit timestamp and UTC offset required')
    stamp = datetime.fromisoformat(value)
    if local_zone and stamp.astimezone(ZoneInfo(local_zone)).utcoffset() != stamp.utcoffset():
        raise ValueError('Timestamp conflicts with declared timezone')
    return stamp


def publication_bound(source):
    """A date-only publication cannot be timed within that calendar day."""
    value, precision = source['published_at'], source['published_at_precision']
    if value is None:
        return None
    if precision == 'date':
        if not re.fullmatch(r'\d{4}-\d\d-\d\d', value):
            raise ValueError('Invalid date precision')
        return datetime.combine(date.fromisoformat(value)+timedelta(days=1), time(), ZoneInfo(source['timezone']))
    stamp = instant(value, local_zone=source['timezone'])
    if precision == 'minute':
        if stamp.second or stamp.microsecond:
            raise ValueError('Invalid minute precision')
        return stamp + timedelta(minutes=1)
    if precision != 'second' or stamp.microsecond:
        raise ValueError('Invalid source time precision')
    return stamp


def append_source_version(event, source):
    """Group by explicit curated event identity. A changed body at one URL appends a version."""
    if source['event_id'] != event['event_id']:
        raise ValueError('Source belongs to a different event')
    if not re.fullmatch(r'[a-f0-9]{64}', source['sha256']):
        raise ValueError('Invalid source SHA256')
    observed = instant(source['captured_at'])
    publication_bound(source)
    versions = [s for s in event['sources'] if s['url'] == source['url']]
    if versions:
        previous = versions[-1]
        prior_time = instant(previous['captured_at'])
        if observed < prior_time or (observed == prior_time and previous['sha256'] != source['sha256']):
            raise ValueError('Ambiguous or out-of-order source revision')
        if previous['sha256'] == source['sha256']:
            return previous['source_version_id']
    revision = len(versions)+1
    key = hashlib.sha256(f"{source['url']}|{revision}|{source['sha256']}".encode()).hexdigest()
    event['sources'].append(dict(deepcopy(source), source_version_id=key, revision=revision))
    return key


def select_as_of(ledger, decision_at):
    """Return only eligible version payloads and their referenced evidence at the decision instant."""
    cutoff = instant(decision_at)
    results, event_ids = [], set()
    for event in ledger['events']:
        event_id = event['event_id']
        if event_id in event_ids:
            raise ValueError('Duplicate event identity')
        event_ids.add(event_id)
        sources = {s['source_version_id']:s for s in event['sources']}
        if len(sources) != len(event['sources']):
            raise ValueError('Duplicate source version')
        best = None
        for expected, version in enumerate(event['versions'], start=1):
            if version['revision'] != expected:
                raise ValueError('Missing or duplicate event revision')
            if version['signal_eligible'] is not True:
                continue
            receipt, ready = version['received_at'], version['feature_ready_at']
            dependency_times = version['dependency_ready_at']
            refs = version['source_version_ids']
            if not receipt or not ready or not isinstance(dependency_times, list) or not refs:
                continue
            received, available = instant(receipt), instant(ready)
            if received > available:
                raise ValueError('Feature ready before receipt')
            if available > cutoff or any(v is None for v in dependency_times):
                continue
            if any(instant(v) > cutoff for v in dependency_times):
                continue
            evidence = [sources[s] for s in refs]
            bounds = [publication_bound(s) for s in evidence]
            if any(bound is None or bound > cutoff for bound in bounds):
                continue
            if any(instant(s['captured_at']) > cutoff for s in evidence):
                continue
            if any(instant(s['captured_at']) > available for s in evidence):
                raise ValueError('Feature ready before its source was captured')
            best = dict(event_id=event_id, theme_id=event['theme_id'], **deepcopy(version),
                        sources=deepcopy(evidence))
        if best is not None:
            results.append(best)
    return results


def checked(path, expected):
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError(f'Evidence digest mismatch: {path.name}')
    return body


def build_pilot(root):
    root = Path(root)
    folder = root/SNAPSHOT
    manifest = json.loads(checked(folder/'manifest.json', SNAPSHOT_SHA))
    for name, digest in manifest.items():
        checked(folder/name, digest)
    seed = json.loads(checked(root/SEED, SEED_SHA))
    records = {r['name']:r for r in json.loads((folder/'requests.json').read_bytes())}
    first, second = deepcopy(seed['events'])
    first['sources'].insert(0, dict(url='https://www.news.cn/20261106/84f141de4c884bf6b250edcbb5b32952/c.html',
        publisher='新华网', origin='新华社', role='original', published_at='2026-11-06T20:59:46+08:00',
        published_at_precision='second', evidence_locator='页面时间及11月6日会议的资本市场段落。'))
    pages = [('xinhua_1106','mofcom_1107'), ('xinhua_1127','csrc_1127')]
    for event, names in zip((first, second), pages, strict=True):
        original = event['sources']
        event['sources'] = []
        refs = []
        for name, source in zip(names, original, strict=True):
            record = records[name]
            path = folder/(name+'.body')
            raw = checked(path, record['sha256']).decode('utf-8')
            pub = source['published_at']
            date_fragment = pub[:10]
            time_fragment = pub.split('T')[1].split('+')[0] if 'T' in pub else ''
            if (record['status'] != 200 or record['curl_exit'] or record['error']
                    or record['url'] != source['url'] or record['final_url'] != source['url']
                    or instant(record['completed_at_utc']) < instant(record['requested_at_utc'])
                    or date_fragment not in raw or time_fragment not in raw or '资本市场稳市机制' not in raw):
                raise ValueError('Official evidence did not match: '+name)
            refs.append(append_source_version(event, dict(source, event_id=event['event_id'],
                timezone='Asia/Shanghai', captured_at=record['completed_at_utc'], sha256=record['sha256'],
                http_status=record['status'], snapshot_body=path.relative_to(root).as_posix())))
        event['versions'] = [dict(revision=1, source_version_ids=refs, received_at=None, feature_ready_at=None,
            dependency_ready_at=[], signal_eligible=False,
            fields={k:deepcopy(event[k]) for k in ('stage','event_time','effective_at',
                'observed_policy_directions','text_increment','comparison_event_id',
                'disclosed_incremental_funding_cny','execution_amount_cny','expectation_surprise')})]
    return dict(schema_version=1, timezone='Asia/Shanghai', events=[first,second],
                source_manifest=SNAPSHOT+'/manifest.json', source_manifest_sha256=SNAPSHOT_SHA,
                scope='仅用于政策资料核对。网页时间、这次取回时间与历史系统收报时间分别记录。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--decision-at')
    args = parser.parse_args()
    ledger = build_pilot(args.root)
    print(json.dumps(select_as_of(ledger, args.decision_at) if args.decision_at else ledger,
                     ensure_ascii=False, indent=2))
