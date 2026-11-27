"""Discover the next annual exchange notices and retain the official search evidence."""
import argparse
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode, urljoin
from uuid import uuid4

from capture_exchange_calendar import capture as capture_annual
from etf_research.evidence_archive import capture as archive, verify as verify_archive
from etf_research.exchange_calendar import BASE_PATH, SOURCES, calendar_at, official_url, verify_annual
from etf_research.http_capture import fetch, load_policy, save_transport
from etf_research.observation_slots import timer_identity
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, lock, read, seal, sha, sync_dir, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
LOG = 'reports/research-calendar-watch'
TIMER = 'etf-research-calendar-watch.timer'
SSE = 'https://www.sse.com.cn/disclosure/dealinstruc/closed/list/'
SZSE = 'https://www.szse.cn/api/search/content'
SZSE_INDEX = 'https://www.szse.cn/disclosure/notice/general/index.html'
ERRORS = (OSError, ValueError, KeyError, TypeError, AttributeError, ArithmeticError)
BINDINGS = (
    BASE_PATH,'config/research_observation.json','scripts/discover_exchange_calendar.py',
    'scripts/capture_exchange_calendar.py','src/etf_research/exchange_calendar.py',
    'src/etf_research/http_capture.py','deploy/etf-research-calendar-watch.service',
    'deploy/etf-research-calendar-watch.timer',
)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attributes = dict(attrs)
            self.links.append((attributes.get('href',''),attributes.get('title','')))


def now():
    return datetime.now(timezone.utc)


def search_form(year):
    return urlencode({'keyword':f'{year}年部分节假日休市安排','time':0,'range':'title',
                      'channelCode[]':'general_news','currentPage':1,'pageSize':20,'scope':0,'endTime':0})


def normalized_title(text):
    return re.sub(r'\s+','',unescape(re.sub(r'<[^>]+>','',text)))


def matches_title(text,year):
    return bool(re.fullmatch(fr'关于(?:(?:上海|深圳)证券交易所)?{year}年(?:部分)?节假日休市安排的(?:公告|通知)',
                             normalized_title(text)))


def candidates(name,raw,year,observed):
    if name=='sse':
        links = Links()
        links.feed(raw.decode('utf-8'))
        pairs = [(urljoin(SSE,href),title) for href,title in links.links]
        if not any(official_url('sse',url) for url,_ in pairs):
            raise ValueError('Official announcements absent from the Shanghai index')
    else:
        data = json.loads(raw)
        rows = data['data']
        pages = (1,) if rows else (0,1)
        if (data['pageSize']!=20 or data['currentPage'] not in pages or not isinstance(rows,list)
                or type(data['totalSize']) is not int or data['totalSize']!=len(rows)):
            raise ValueError('Shenzhen title search is incomplete or changed format')
        pairs = []
        for row in rows:
            if row['chnlcode']!='general_news' or type(row['docpubtime']) is not int:
                raise ValueError('Shenzhen title search returned an unbound listing')
            address = row['docpuburl']
            # Website search sometimes advertises an HTTP link for the same public notice.
            if address.startswith('http://www.szse.cn/'):
                address = 'https://'+address.removeprefix('http://')
            if datetime.fromtimestamp(row['docpubtime']/1000,timezone.utc)>observed:
                raise ValueError('Shenzhen notice is timestamped after capture')
            pairs.append((address,row['doctitle']))
    found = {url:normalized_title(title) for url,title in pairs
             if official_url(name,url) and matches_title(title,year)}
    return [dict(url=url,title=title) for url,title in sorted(found.items())]


def index_results(folder,year,checked):
    started = instant(read(folder/'started.json')['startedAt'])
    rows = read(folder/'requests.json')
    if [row['name'] for row in rows]!=['sse','szse']:
        raise ValueError('Unexpected official index inventory')
    sources = {}
    for row in rows:
        name = row['name']
        url = SSE if name=='sse' else SZSE
        body = folder/(name+'.body')
        received = instant(row['receivedAt'])
        if (row['url']!=url or row['sha256']!=sha(body) or row['bytes']!=body.stat().st_size
                or not started<=instant(row['requested_at_utc'])<=received<=checked
                or name=='szse' and (row.get('request_method'),row.get('request_body'),row.get('request_referer'))
                !=('POST',search_form(year),SZSE_INDEX)):
            raise ValueError('Official search response is not bound to the request')
        record = dict(url=url,receivedAt=row['receivedAt'],httpStatus=row['status'],sha256=row['sha256'],
                      status='unavailable',candidates=[])
        if (row['status']==200 and not row['curl_exit'] and not row.get('error')
                and row['final_url']==url and row['metrics']['ssl_verify_result']==0):
            try:
                matched = candidates(name,body.read_bytes(),year,received)
                record.update(candidates=matched,status='ambiguous' if len(matched)>1 else
                              'candidate' if matched else 'not_listed')
            except ERRORS as error:
                record['issue'] = str(error)[:250]
        sources[name] = record
    return sources


def inspect(folder,year,checked):
    sources = index_results(folder,year,checked)
    annual = folder/'annual'
    status = 'waiting_for_both_exchanges'
    verified = None
    paired = all(source['status']=='candidate' for source in sources.values())
    if paired and (annual/'calendar.json').is_file():
        observation = verify_annual(annual)
        expected = {name:row['candidates'][0]['url'] for name,row in sources.items()}
        observed = {request['name']:request['url'] for request in read(annual/'requests.json')}
        if expected!=observed or observation['year']!=year or instant(observation['checkedAt'])>checked:
            raise ValueError('Annual documents differ from discovered URLs or capture date')
        status = 'annual_pair_verified'
        verified = sha(annual/'manifest.json')
    elif paired:
        status = 'annual_pair_unverified'
    elif any(src['status'] in ('unavailable','ambiguous') for src in sources.values()):
        status = 'source_discovery_incomplete'
    return dict(schemaVersion=1,year=year,checkedAt=checked.isoformat(),
                status=status,sources=sources,annualManifestSha256=verified)


def collect(folder,year,*,trigger=None):
    folder.mkdir(parents=True,exist_ok=False)
    policy = load_policy()
    save_transport(folder,policy)
    begin = dict(year=year,startedAt=now().isoformat())
    if trigger is not None:
        begin['trigger'] = trigger
    create(folder/'started.json',begin)
    sse = fetch(folder,'sse',SSE,policy)
    sse['receivedAt'] = now().isoformat()
    szse = fetch(folder,'szse',SZSE,policy,additional_hosts=(SOURCES['szse'],),
                 post_data=search_form(year),referer=SZSE_INDEX)
    szse['receivedAt'] = now().isoformat()
    create(folder/'requests.json',[sse,szse])
    sources = index_results(folder,year,now())
    if all(row['status']=='candidate' for row in sources.values()):
        try:
            capture_annual(folder/'annual',year,{name:row['candidates'][0]['url'] for name,row in sources.items()})
        except ERRORS as error:
            create(folder/'annual-error.json',dict(error=str(error)[:300],checkedAt=now().isoformat()))
    result = inspect(folder,year,now())
    create(folder/'result.json',result)
    seal(folder)
    return verify(folder)


def verify(folder):
    verify_bundle(folder)
    outcome = read(folder/'result.json')
    year = read(folder/'started.json')['year']
    if outcome!=inspect(folder,year,instant(outcome['checkedAt'])):
        raise ValueError('Calendar discovery did not reproduce')
    return outcome


def target_year(calendar,observed):
    local = observed.astimezone(TZ)
    return local.year+1 if str(local.year) in calendar.ranges and local.month>=11 else local.year


def watch(root,store,trigger,started):
    calendar = calendar_at(root,started)
    year = target_year(calendar,started)
    if str(year) in calendar.ranges:
        return dict(year=year,status='no_pending_calendar_in_scope')
    with lock(root/'.runtime/calendar-watch.lock'):
        stamp = started.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8]
        folder = root/LOG/str(year)/stamp
        records = folder/'records'
        outcome = collect(records,year,trigger=trigger)
        bounds = [p.relative_to(root).as_posix() for p in records.rglob('*') if p.is_file()]
        captured = archive(root,store,[*bounds,*BINDINGS])
        safe = verify_archive(store,captured['snapshot'])
        relative = folder.relative_to(root).as_posix()
        if safe['files'][relative+'/records/manifest.json']['sha256']!=sha(records/'manifest.json'):
            raise ValueError('Calendar watch archive did not bind its evidence')
        receipt = dict(schemaVersion=1,path=relative,year=year,status=outcome['status'],trigger=trigger,
                       archiveSha256=captured['snapshot'],manifestSha256=sha(records/'manifest.json'),
                       archiveVerifiedAt=now().isoformat())
        create(folder/'receipt.json',receipt)
        sync_dir(folder)
        return dict(outcome,receipt=receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--run',action='store_true')
    action.add_argument('--year',type=int)
    action.add_argument('--verify',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--archive-store',type=Path)
    args = parser.parse_args()
    if args.run:
        trigger = timer_identity(os.environ,TIMER)
        if trigger is None or args.archive_store is None:
            parser.error('An official calendar watch run requires its systemd timer and archive store')
        result = watch(ROOT,args.archive_store.resolve(),trigger,now())
    elif args.verify:
        result = verify(args.verify)
    elif args.output is None or not 2000<=args.year<=2100:
        parser.error('Manual discovery requires --year 2000–2100 and a new --output directory')
    else:
        result = collect(args.output,args.year)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    main()
