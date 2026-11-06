"""Offline audit of captured SSE responses; absence never authorizes a fill."""
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import argparse, hashlib, json, math
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'data/snapshots/2026-11-06-suspension-15'

def validate(meta, body, complete=True):
    def require(ok, message):
        if not ok: raise ValueError(message)
    require(meta['status'] == 200 and not meta.get('error'), 'Failed request')
    require(hashlib.sha256(body).hexdigest() == meta['sha256'], 'Body hash mismatch')
    u = urlparse(meta['url']); q = parse_qs(u.query, keep_blank_values=True)
    require(u.scheme == 'https' and u.netloc == 'query.sse.com.cn' and u.path == '/sseQuery/commonSoaQuery.do', 'Wrong endpoint')
    require(meta['final_url'] == meta['url'], 'Unexpected redirect')
    require(q['sqlId'] == ['SSE_PL_JYTS_TFPXX_JJ'], 'Wrong query')
    start, end = (datetime.strptime(q[k][0], '%Y%m%d').date() for k in ('startDate', 'endDate'))
    captured = datetime.fromisoformat(meta['requested_at_utc'])
    require(captured.tzinfo is not None and start <= end < captured.date(), 'Uncompleted or invalid query interval')
    d = json.loads(body); p = d['pageHelp']; rows = d['result']
    require(not d.get('actionErrors') and not d.get('fieldErrors') and d['sqlId'] == q['sqlId'][0], 'API error')
    size = int(q['pageHelp.pageSize'][0]); total = p['total']
    require(type(total) is int and total >= 0 and size > 0, 'Invalid total')
    require(q['pageHelp.pageNo'] == ['1'] and p['pageNo'] == 1 and p['pageSize'] == size, 'Wrong page')
    require(p['pageCount'] == math.ceil(total / size) and len(rows) == min(total, size) and rows == p['data'], 'Page inconsistency')
    require(not complete or total == len(rows), 'Incomplete pagination')
    for row in rows:
        require(not q['secCode'][0] or row['secCode'] == q['secCode'][0], 'Wrong security')
        a = datetime.strptime(row['startStopDate'], '%Y%m%d').date()
        b = datetime.strptime(row['endStopDate'], '%Y%m%d').date() if row['endStopDate'] else None
        require(b is None or a <= b, 'Invalid event dates')
        require(a <= end and (b is None or b >= start), 'Event outside query interval')
        # Empty end remains unknown; never substitute the query end or assume trading status.
    return rows, total

def audit():
    records = sum((json.loads((SNAPSHOT/n).read_text()) for n in ('requests.json', 'followup_requests.json')), [])
    by_name = {}; totals = {}
    for m in records:
        name = m['name']
        if name in by_name: raise ValueError('Duplicate request name')
        by_name[name], totals[name] = validate(m, (SNAPSHOT/(name+'.body')).read_bytes(), not name.startswith('control_'))
    annual = []; all_rows = []
    for year in range(2018, 2027):
        rows = by_name[f'all_{year}']; control = by_name[f'control_{year}']
        assert rows and rows[:25] == control and totals[f'control_{year}'] == len(rows)
        assert not any(r['secCode'] in ('510300','511010') for r in rows)
        annual.append({'year':year,'returned_rows':len(rows),'complete_under_reported_total':True,'target_matches':0})
        all_rows.extend(rows)
        for symbol in ('510300','511010'): assert not by_name[f'year_{symbol}_{year}']
    for symbol in ('510300','511010'):
        assert not by_name[f'full_{symbol}'] and not by_name[f'lookback_{symbol}']
    overlap = by_name['overlap_inside']
    assert len(overlap) == 1 and overlap == by_name['overlap_with_start']
    assert overlap[0]['startStopDate'] < '20210101' and overlap[0]['endStopDate'] > '20210131'
    unique = {json.dumps(r, sort_keys=True, ensure_ascii=False) for r in all_rows}
    return {'snapshot':str(SNAPSHOT.relative_to(ROOT)), 'requests':len(records), 'http_200':len(records),
        'query_end':'2026-11-05', 'annual':annual, 'queried_rows':len(all_rows),
        'distinct_full_records':len(unique), 'repeated_record_appearances':len(all_rows)-len(unique),
        'open_end_distinct_records':[json.loads(r) for r in sorted(unique) if not json.loads(r)['endStopDate']],
        'cross_year_overlap_control':overlap, 'target_returned_records':0,
        'absence_proves_no_suspensions':False, 'changes_account_or_execution_permissions':False,
        'limitations':['Completeness is relative to this API reported totals, not an independent historical census.',
          'Identical full records are deduplicated only for counting; these are not necessarily distinct trading halts.',
          'Legacy and unknown type codes remain unclassified; creation/redemption events are not trading-halt proof.',
          'An empty end date remains unknown. One overlap control does not prove all interval semantics.',
          'No current-day quotes or account updates are included.']}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,default=ROOT/'reports/2026-11-06-suspension/audit.json'); args=p.parse_args()
    result=audit(); args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print('Suspension evidence audit passed:',result['requests'],'responses;',result['distinct_full_records'],'distinct records')
if __name__ == '__main__': main()
