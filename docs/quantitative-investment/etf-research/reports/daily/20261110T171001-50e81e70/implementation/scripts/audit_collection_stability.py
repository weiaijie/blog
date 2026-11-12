"""Audit completed same-day live-source rounds; never infer long-term uptime."""
from pathlib import Path
from datetime import datetime
import argparse,json,statistics,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from etf_research.publication import read,sha,create,verify_bundle,inside
from etf_research.data import verify_manifest

def audit(since,baseline,min_rounds):
    expected=read(ROOT/baseline);rows=[];unfinished=[];attempts=[];catalog_times=[]
    for folder in sorted((ROOT/'reports/daily').iterdir()):
        if not (folder/'started.json').exists():continue
        start=read(folder/'started.json')
        if datetime.fromisoformat(start['created_at_shanghai'])<since or start['offline_replay']:continue
        if not (folder/'manifest.json').exists():
            unfinished.append(dict(bundle=str(folder.relative_to(ROOT)),failure=read(folder/'failure.json') if (folder/'failure.json').exists() else 'incomplete'))
            continue
        verify_bundle(folder);state=read(folder/'forward_checkpoint.json')
        if state!=expected:raise ValueError('Same-day acceptance changed the account')
        admitted=read(folder/'admission.json');official=folder.name+'-official';price=admitted['snapshot'];round_attempts=[]
        for label in [price,official]:
            snapshot=ROOT/'data/snapshots'/label;verify_manifest(snapshot)
            policy=read(snapshot/'transport_policy.json')
            if policy['address_family']!='ipv4':raise ValueError('Unexpected transport in acceptance')
            records=read(snapshot/'requests.json')
            if label==price:
                config=read(snapshot/'config.json')
                selected={name for providers in config['prices'].values() for name in providers.values()}|{'catalog_510300','catalog_511010'}
            else:selected={'sse_'+kind+'_'+symbol for kind in ('dayk','snap') for symbol in ('510300','511010')}
            if not selected.issubset({r['name'] for r in records}):raise ValueError('Selected request missing')
            for logical in records:
                if logical['name'] in selected and (logical['status']!=200 or logical.get('error') or logical['address_family']!='ipv4'):raise ValueError('Failed selected response')
                if logical['actual_requests']!=len(logical['attempts']):raise ValueError('Attempt count mismatch')
                last=logical['attempts'][-1]
                if logical['selected_attempt']!=last['name'] or logical['sha256']!=last['sha256']:raise ValueError('Selected response mismatch')
                for attempt in logical['attempts']:
                    if sha(snapshot/(attempt['name']+'.body'))!=attempt['sha256']:raise ValueError('Attempt body changed')
                    if attempt['curl_exit']==0 and attempt['status']==200 and attempt['metrics']['ssl_verify_result']!=0:raise ValueError('TLS validation failed')
                    item=dict(snapshot=label,logical=logical['name'],attempt=attempt['name'],status=attempt['status'],curl_exit=attempt['curl_exit'],elapsed_seconds=attempt['elapsed_seconds'])
                    attempts.append(item);round_attempts.append(item)
                    if logical['name'].startswith('catalog_') and attempt['status']==200:catalog_times.append(attempt['elapsed_seconds'])
        rows.append(dict(bundle=str(folder.relative_to(ROOT)),created_at_shanghai=start['created_at_shanghai'],price_snapshot=price,official_snapshot=official,catalog_counts=admitted['official_catalog_counts'],actual_requests=len(round_attempts),checkpoint_unchanged=True))
    if len(rows)<min_rounds:raise ValueError('Not enough completed live-source rounds')
    operations=[]
    for path in sorted((ROOT/'reports/operations').glob('*/result.json')):
        result=read(path)
        if datetime.fromisoformat(result['started_at_utc'])>=since:
            verify_bundle(path.parent);operations.append({k:result[k] for k in ('operation','mode','phase','exit_code','started_at_utc','finished_at_utc','account_changed','scheduler')})
    return dict(schema_version=1,acceptance='bounded same-day live-source engineering test, not multi-day uptime',since=since.isoformat(),baseline=baseline,
        admitted_rounds=len(rows),rounds=rows,failed_or_incomplete_live_rounds=unfinished,actual_requests=len(attempts),
        failed_attempts=[x for x in attempts if x['status']!=200 or x['curl_exit']!=0],
        catalog_successful_attempts=len(catalog_times),catalog_elapsed_median_seconds=statistics.median(catalog_times),catalog_elapsed_max_seconds=max(catalog_times),
        observation_span_seconds=(datetime.fromisoformat(rows[-1]['created_at_shanghai'])-datetime.fromisoformat(rows[0]['created_at_shanghai'])).total_seconds(),
        new_forward_observations=0,checkpoint_sha256=expected['checkpoint_sha256'],operations=operations)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--since',type=datetime.fromisoformat,required=True);p.add_argument('--baseline',default='reports/2026-11-06-close/forward_checkpoint.json');p.add_argument('--min-rounds',type=int,default=5);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.since.tzinfo is None:raise ValueError('Timezone-aware start required')
    result=audit(a.since,a.baseline,a.min_rounds);create(a.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rounds','operations')},ensure_ascii=False))
