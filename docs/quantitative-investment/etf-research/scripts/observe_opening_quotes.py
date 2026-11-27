"""Archive SSE evidence of the opening auction result for the independent simulation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import re
from uuid import uuid4

from collect_sse_research_day import CALENDAR_SHA
from etf_research.admission import sessions_between
from etf_research.baselines import SYMBOLS
from etf_research.evidence_archive import capture, verify as verify_archive
from etf_research.http_capture import fetch, load_policy, save_transport
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, lock, read, seal, sha, sync_dir, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
TIMER = 'etf-research-opening.timer'
LOG = 'reports/research-opening'
PROBES = 'reports/research-opening-probes'
CALENDAR = 'data/snapshots/2026-11-04-calendar-08/calendar.json'
QUOTE = 'https://yunhq.sse.com.cn:32042/v1/sh1/snap/'
FIELDS = '?select=name,prev_close,open,high,low,last,up_limit,down_limit,tradephase,hlt_tag'
FIRST, END = time(9,25), time(9,30)
SLOTS = (time(9,26),time(9,28))
TICK = Decimal('.001')


def now():
    return datetime.now(timezone.utc)


def request_url(symbol):
    return QUOTE+symbol+FIELDS


def trigger_event(env):
    invocation = env.get('INVOCATION_ID','')
    stamp = env.get('TRIGGER_TIMER_REALTIME_USEC','')
    if env.get('TRIGGER_UNIT')==TIMER and re.fullmatch('[a-f0-9]{32}',invocation) and stamp.isdecimal():
        return dict(unit=TIMER,id=invocation,realtimeUsec=int(stamp))
    return None


def scheduled_opening(trigger, started):
    if not trigger or trigger['unit']!=TIMER:
        return False
    local = started.astimezone(TZ)
    stamp = datetime.fromtimestamp(trigger['realtimeUsec']/1_000_000,TZ)
    clock = stamp.replace(second=0,microsecond=0)
    return clock.time() in SLOTS and clock<=stamp<=local<clock+timedelta(minutes=1)


def decimal_price(value):
    if isinstance(value,bool) or not isinstance(value,(int,Decimal,str)):
        raise ValueError('Unknown price representation')
    result = Decimal(value)
    if not result.is_finite() or result<=0 or result%TICK:
        raise ValueError('Invalid auction price or tick')
    return result


def quote_state(folder, row, symbol, day, started, finished):
    body = folder/(symbol+'.body')
    if (row['url']!=request_url(symbol) or row['final_url']!=request_url(symbol) or
            row['sha256']!=sha(body) or row['status']!=200 or row['curl_exit'] or row.get('error') or
            row['certificate_verification_enabled'] is not True):
        raise ValueError('Opening response or source did not verify')
    requested = instant(row['requested_at_utc']).astimezone(TZ)
    data = json.loads(body.read_bytes(),parse_float=Decimal)
    raw_time = data['time']
    if type(raw_time) is not int or not 0<=raw_time<=235959:
        raise ValueError('Missing exchange opening timestamp')
    exchange_time = datetime.combine(day,datetime.strptime(f'{raw_time:06d}','%H%M%S').time(),TZ)
    if (data['code']!=symbol or data['date']!=int(day.strftime('%Y%m%d')) or
            not started<=requested<=finished or not FIRST<=requested.time()<END or
            not FIRST<=exchange_time.time()<END or exchange_time>finished):
        raise ValueError('Wrong instrument, stale quote or quote outside opening auction window')
    snap = data['snap']
    if not isinstance(snap,list) or len(snap)!=10 or not isinstance(snap[8],str):
        raise ValueError('Invalid opening quote fields')
    phase = snap[8]
    clocks = dict(exchangeAt=exchange_time.isoformat(),requestedAt=requested.isoformat())
    if phase.startswith('P01'):
        return dict(status='blocked',phase=phase,**clocks)
    if not phase.startswith('T11') or snap[9]!='':
        raise ValueError('Trading phase does not establish a completed auction')
    previous, opened, high, low, last = map(decimal_price,snap[1:6])
    if not opened==high==low==last:
        raise ValueError('Opening snapshot prices do not isolate the auction')
    return dict(status='tradable',openingPrice=str(opened),reference=str(previous),phase=phase,**clocks)


def assess(folder, day, started, finished):
    rows = read(folder/'requests.json')
    if len(rows)!=len(SYMBOLS) or {row['name'] for row in rows}!=set(SYMBOLS):
        raise ValueError('Wrong opening collection instrument set')
    result = {}
    for row in rows:
        symbol = row['name']
        try:
            result[symbol] = quote_state(folder,row,symbol,day,started,finished)
        except (OSError,ValueError,KeyError,TypeError,ArithmeticError) as error:
            result[symbol] = dict(status='unknown',reason=str(error)[:240])
    return result


def verify_opening(root, store, attempt):
    attempt = attempt.resolve()
    records = attempt/'records'
    verify_bundle(records)
    receipt = read(attempt/'receipt.json')
    result = read(records/'capture.json')
    archive = verify_archive(store,receipt['archiveSha256'])
    folder = attempt.parent.parent
    day = datetime.fromisoformat(result['day']).date()
    called, finished, ready = map(instant,(result['startedAt'],result['finishedAt'],receipt['archiveVerifiedAt']))
    if (attempt.parent.name!=str(day) or folder not in (root/LOG,root/PROBES) or
            receipt['path']!=attempt.relative_to(root).as_posix() or receipt['manifestSha256']!=sha(records/'manifest.json') or
            not called<=finished<=instant(archive['created_at_utc'])<=ready<=now() or
            result['quotes']!=assess(records,day,called,finished)):
        raise ValueError('Opening capture and receipt do not reproduce')
    for path in records.iterdir():
        if archive['files'][path.relative_to(root).as_posix()]['sha256']!=sha(path):
            raise ValueError('Opening archive bytes differ')
    live = folder==root/LOG and scheduled_opening(result['trigger'],called) and result['trigger']['id']==attempt.name
    return dict(**receipt,quotes=result['quotes'],scheduled=live)


def collect(root, store, *, probe):
    root,store=root.resolve(),store.resolve()
    started=now()
    local=started.astimezone(TZ)
    day=local.date()
    trigger=None if probe else trigger_event(os.environ)
    if not probe and trigger is None:
        raise ValueError('Opening collection requires scheduled provenance')
    calendar=root/CALENDAR
    if sha(calendar)!=CALENDAR_SHA:
        raise ValueError('Opening calendar digest mismatch')
    if not sessions_between(read(calendar)['holiday_ranges'],day,day):
        return dict(status='not_scheduled',day=str(day))
    if not probe and not scheduled_opening(trigger,started):
        return dict(status='missed_opening_slot',day=str(day),startedAt=started.isoformat())
    identity=started.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8] if probe else trigger['id']
    with lock(root/'.runtime/research-opening.lock'):
        attempt=root/(PROBES if probe else LOG)/str(day)/identity
        records=attempt/'records'
        records.mkdir(parents=True,exist_ok=False)
        policy=dict(load_policy(root/'config/collection.json'),max_attempts=2,
                    connect_timeout_seconds=5,total_timeout_seconds=12,
                    backoff_seconds=[2],max_retry_after_seconds=8)
        save_transport(records,policy)
        with ThreadPoolExecutor(max_workers=2) as pool:
            requests=list(pool.map(lambda symbol:fetch(records,symbol,request_url(symbol),policy),SYMBOLS))
        create(records/'requests.json',requests)
        finished=now()
        quotes=assess(records,day,started,finished)
        create(records/'capture.json',dict(day=str(day),startedAt=started.isoformat(),finishedAt=finished.isoformat(),
                                           trigger=trigger,quotes=quotes))
        seal(records)
        names=[p.relative_to(root).as_posix() for p in records.iterdir()]
        names.extend(('scripts/observe_opening_quotes.py',CALENDAR,'config/collection.json'))
        archive=capture(root,store,names)
        verify_archive(store,archive['snapshot'])
        receipt=dict(path=attempt.relative_to(root).as_posix(),archiveSha256=archive['snapshot'],
                     archiveVerifiedAt=now().isoformat(),manifestSha256=sha(records/'manifest.json'))
        create(attempt/'receipt.json',receipt)
        for folder in (attempt,attempt.parent,attempt.parent.parent):
            sync_dir(folder)
        return verify_opening(root,store,attempt)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--run',action='store_true')
    modes.add_argument('--probe',action='store_true')
    modes.add_argument('--verify',type=Path)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--archive-store',type=Path,required=True)
    args=parser.parse_args()
    root=args.observation_root.resolve()
    result=(verify_opening(root,args.archive_store.resolve(),args.verify) if args.verify else
            collect(root,args.archive_store,probe=args.probe))
    print(json.dumps(result,ensure_ascii=False))
