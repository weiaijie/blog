"""Versioned annual exchange calendars, admitted by evidence and actual local cutoff."""
from dataclasses import dataclass
from datetime import date, timedelta
import hashlib
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit

from .evidence_archive import safe_path
from .policy_events import instant
from .publication import encoded, read, sha, verify_bundle

BASE_PATH = 'data/snapshots/2026-11-04-calendar-08/calendar.json'
BASE_SHA = '950a3bfe2bab7ad484abc03aa27207bc70a49a4a144f495899cf1bd2aa10c8c6'
REGISTRY = 'data/reference/calendar-years'
LOADER = 'src/etf_research/exchange_calendar.py'
SOURCES = {'sse':'www.sse.com.cn','szse':'www.szse.cn'}
HOLIDAYS = frozenset(('元旦','春节','清明节','劳动节','端午节','中秋节','国庆节'))
DATE = r'(?:\d{4}年)?\d{1,2}月\d{1,2}日'
STAMP = DATE+r'(?:[（(]星期[一二三四五六日天][）)])?'
CLAUSE = re.compile(fr'^(?P<lower>{STAMP})(?:至(?P<upper>{STAMP}))?休市[，,。]'
                    fr'(?P<opens>{STAMP})(?:起)?照常开市(?:[。；;]|$)')
WEEKDAYS = '一二三四五六日'
WEEKEND_NOTE = re.compile(fr'另外[，,](?P<days>{STAMP}(?:[、，,]{STAMP})*)为周末休市[。；;]?')


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.ignored = False

    def handle_starttag(self, tag, attributes):
        if tag in ('script','style'):
            self.ignored = True

    def handle_endtag(self, tag):
        if tag in ('script','style'):
            self.ignored = False

    def handle_data(self, data):
        if not self.ignored:
            self.text.append(data)


def official_url(name,url):
    parts = urlsplit(url)
    path = (r'/disclosure/announcement/general/c/c_\d{8}_\d+\.shtml' if name=='sse'
            else r'/disclosure/notice/(?:general/)?t\d{8}_\d+\.html')
    return parts.scheme=='https' and parts.netloc==SOURCES[name] and not parts.query and not parts.fragment and (
        re.fullmatch(path,parts.path) is not None)


def notice_day(text, year):
    pieces = re.fullmatch(r'(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日(?:[（(]星期([一二三四五六日天])[）)])?',text)
    explicit,month,day,weekday = pieces.groups()
    actual = date(year if explicit is None else int(explicit),int(month),int(day))
    if weekday is not None and WEEKDAYS[actual.weekday()] != weekday.replace('天','日'):
        raise ValueError('Official notice weekday does not match the date')
    return actual


def parse_notice(name, body, year):
    parser = VisibleText()
    parser.feed(body.decode('utf-8-sig'))
    text = re.sub(r'\s+','', ''.join(parser.text))
    title_prefix = '关于上海证券交易所' if name=='sse' else '关于'
    section = re.search(r'一、休市安排(.+?)二、',text)
    if title_prefix+str(year)+'年部分节假日休市安排的通知' not in text or section is None:
        raise ValueError('Unrecognized annual exchange notice title or section')
    entries = re.split(r'[（(][一二三四五六七八九十]+[）)]',section[1])
    if entries[0]:
        raise ValueError('Unparsed exchange closure notice header')
    ranges = []
    seen = set()
    for entry in entries[1:]:
        names,details = re.split('[：:]',entry,maxsplit=1)
        holidays = set(re.split('[、及和]',names))
        match = CLAUSE.match(details)
        if not holidays <= HOLIDAYS or holidays & seen or not match:
            raise ValueError('Unrecognized or repeated exchange holiday')
        seen.update(holidays)
        note = details[match.end():]
        if note:
            weekend = WEEKEND_NOTE.fullmatch(note)
            if weekend is None or any(notice_day(day,year).weekday()<5 for day in
                                      re.split('[、，,]',weekend['days'])):
                raise ValueError('Unverified additional closure in the annual notice')
        lower = notice_day(match['lower'],year)
        upper = notice_day(match['upper'] or match['lower'],year)
        opens = notice_day(match['opens'],year)
        if not date(year,1,1) <= lower <= upper <= date(year,12,31) or opens <= upper:
            raise ValueError('Exchange closure range or reopening is out of order')
        ranges.append((lower,upper,opens))
    if seen != HOLIDAYS or ranges != sorted(ranges):
        raise ValueError('Annual notice is incomplete or out of order')
    for i,(_,upper,opens) in enumerate(ranges):
        if i+1 < len(ranges) and upper >= ranges[i+1][0]:
            raise ValueError('Exchange closure ranges overlap')
        expected = upper + timedelta(days=1)
        while expected.weekday()>=5 or any(lower<=expected<=end for lower,end,_ in ranges):
            expected += timedelta(days=1)
        if opens != expected:
            raise ValueError('Reported reopening disagrees with the closure ranges')
    return [[lower.strftime('%m-%d'),upper.strftime('%m-%d')] for lower,upper,_ in ranges]


def inspect_annual(folder, year, checked_at):
    rows = read(folder/'requests.json')
    if [row['name'] for row in rows] != list(SOURCES):
        raise ValueError('Two official exchange requests are required')
    versions = {}
    for row in rows:
        name = row['name']
        path = folder/(name+'.body')
        if (not official_url(name,row['url']) or row['url']!=row['final_url']
                or row['status']!=200 or row['curl_exit'] or row.get('error')
                or row['certificate_verification_enabled'] is not True
                or row['metrics']['ssl_verify_result']!=0 or row['sha256']!=sha(path)
                or row['bytes']!=path.stat().st_size
                or not instant(row['requested_at_utc'])<=instant(row['receivedAt'])<=instant(checked_at)):
            raise ValueError('Annual notice transport or timestamp failed: '+name)
        versions[name] = parse_notice(name,path.read_bytes(),year)
    if versions['sse'] != versions['szse']:
        raise ValueError('Official exchange closure ranges disagree')
    return dict(schemaVersion=1,year=year,checkedAt=checked_at,holidayRanges=versions['sse'])


def verify_annual(folder):
    verify_bundle(folder)
    value = read(folder/'calendar.json')
    if value != inspect_annual(folder,value['year'],value['checkedAt']):
        raise ValueError('Annual exchange calendar does not reproduce')
    return value


@dataclass(frozen=True)
class ExchangeCalendar:
    ranges: dict
    digest: str
    files: tuple

    @property
    def extensions(self):
        return self.files[1:]


def base_ranges(path):
    if sha(path)!=BASE_SHA:
        raise ValueError('Legacy exchange calendar checksum mismatch')
    return read(path)['holiday_ranges']


def calendar_at(root, observed, *, pinned=None):
    if observed.utcoffset() is None:
        raise ValueError('Calendar lookup requires an offset-aware clock')
    ranges = base_ranges(root/BASE_PATH)
    files = [BASE_PATH]
    digest = BASE_SHA
    registry = root/REGISTRY
    if pinned == BASE_SHA:
        return ExchangeCalendar(ranges,digest,tuple(files))
    for marker in sorted(registry.glob('*.json')):
        if marker.is_symlink() or not re.fullmatch(r'\d{4}\.json',marker.name):
            raise ValueError('Unexpected annual calendar marker')
        row = read(marker)
        available = instant(row['admittedAt'])
        if available>observed:
            continue
        year = int(marker.stem)
        if row.get('schemaVersion')!=1 or row['year']!=year or year!=max(map(int,ranges))+1:
            raise ValueError('Annual calendars must extend the previous verified year')
        if not re.fullmatch(r'data/snapshots/[^/]+',row['snapshot']):
            raise ValueError('Unsafe annual calendar evidence directory')
        bundle = safe_path(root,row['snapshot'])
        manifest = bundle/'manifest.json'
        if sha(manifest)!=row['manifestSha256']:
            raise ValueError('Annual calendar bundle checksum mismatch')
        entry = verify_annual(bundle)
        if entry['year']!=year or instant(entry['checkedAt'])>available:
            raise ValueError('Annual calendar admitted before verification')
        ranges[str(year)] = entry['holidayRanges']
        digest = hashlib.sha256(encoded([digest,sha(marker),row['manifestSha256']])).hexdigest()
        files.append(marker.relative_to(root).as_posix())
        files.extend(path.relative_to(root).as_posix() for path in sorted(bundle.iterdir()) if path.is_file())
    if pinned is not None and pinned!=digest:
        raise ValueError('No verified calendar matches the pinned fingerprint')
    return ExchangeCalendar(ranges,digest,tuple(files))
