"""Verify captured sources for the separate RMB-listed ETF comparison."""
import hashlib
import json
import re
from datetime import date, datetime
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from pypdf import PdfReader

from etf_research.admission import completed_date, parse_prices
from etf_research.data import RawBar, verify_manifest
from etf_research.long_history import load_long_history
from etf_research.official_history import parse_dayk

ROOT = Path(__file__).resolve().parents[1]
SNAPS = ROOT / 'data/snapshots'
PREFIX = '2026-11-08-markets-051007'
START, END = date(2023, 10, 30), date(2026, 10, 30)


def evidence():
    items = {}
    for suffix in ('', 'b', 'c', 'd'):
        folder = SNAPS / (PREFIX + suffix)
        verify_manifest(folder)
        for r in json.loads((folder / 'requests.json').read_text()):
            key = r['name']
            path = folder / (key + '.body')
            if key in items or hashlib.sha256(path.read_bytes()).hexdigest() != r['sha256']:
                raise ValueError('Source identity or checksum conflict: ' + key)
            items[key] = path, r
    return items


def source(items, key):
    path, r = items[key]
    if (r['status'] != 200 or r['exit_code'] or not r['bytes'] or r['url'] != r['effective_url']
            or completed_date(datetime.fromisoformat(r['requested_at_utc'])) < END):
        raise ValueError('Failed source: ' + key)
    return path


def verified_inputs(items):
    domestic = load_long_history(SNAPS)
    dates = tuple(d for d in domestic.sessions if START <= d <= END)
    bars = dict(domestic.bars)
    for code in ('513500', '159920'):
        market = 'sh' if code == '513500' else 'sz'
        official_url = items['official_'+code][1]['url']
        sina_url = urlparse(items['sina_'+code+'_1970'][1]['url'])
        if (official_url != f'https://yunhq.sse.com.cn:32042/v1/{market}1/dayk/{code}?begin=0&end=-1&period=day'
                or sina_url.hostname != 'quotes.sina.cn' or parse_qs(sina_url.query).get('symbol') != [market+code]
                or items['distribution_'+code][1]['url'] != f'https://fundf10.eastmoney.com/fhsp_{code}.html'):
            raise ValueError('Unbound security identity or venue')
        official = parse_dayk(source(items, 'official_' + code).read_text(), code)
        sina = parse_prices(source(items, 'sina_' + code + '_1970').read_bytes(), 'sina', END)
        for series in (official, sina):
            if tuple(d for d in series if START <= d <= END) != dates:
                raise ValueError('Calendar mismatch: ' + code)
        bars[code] = {d: RawBar(d, **official[d]) for d in dates}
        if any(bars[code][d] != sina[d] for d in dates):
            raise ValueError('Price source disagreement: ' + code)
        extra = ('sohu_all_513500','sohu_513500_2024') if code=='513500' else ('sohu_159920_2025',)
        for key in extra:
            sohu = parse_prices(source(items, key).read_bytes(), 'sohu', END)
            if any(sohu[d] != bars[code][d] for d in sohu if START <= d <= END):
                raise ValueError('Sohu disagreement: '+key)
        vendor = source(items, 'distribution_' + code).read_text().split('权益登记日')[-1].split('分红送配公告')[0]
        expected = {'513500': {'2022-03-29'}, '159920': {'2018-06-22', '2018-06-26'}}
        if set(re.findall(r'\d{4}-\d\d-\d\d', vendor)) != expected[code]:
            raise ValueError('Distribution/split table changed: ' + code)
    sse = json.loads(source(items, 'sse_catalog').read_text())
    notices = sse['result']
    if len({r['URL'] for r in notices}) != len(notices) or len(notices) != sse['pageHelp']['total']:
        raise ValueError('Incomplete SSE catalog')
    cn = []
    for key in ('cninfo_fund', 'cninfo_fund_2', 'cninfo_fund_3', 'cninfo_fund_4'):
        page = json.loads(source(items, key).read_text())
        if page['totalAnnouncement'] != 116:
            raise ValueError('Changed Shenzhen catalog size')
        cn.extend(page['announcements'])
    if len(cn) != 116 or len({a['announcementId'] for a in cn}) != len(cn) or page['hasMore']:
        raise ValueError('Incomplete Shenzhen catalog')
    if any(r['SECURITY_CODE'] != '513500' for r in notices) or any(
            r['secCode'] != '159920' or r['orgId'] != 'jjjl0000031' for r in cn):
        raise ValueError('Wrong security in disclosure catalog')
    for key, catalog, url_key, base_url in [
            ('q3_513500',notices,'URL','https://www.sse.com.cn'),
            ('q3_159920',cn,'adjunctUrl','https://static.cninfo.com.cn/'),
            ('h1_513500',notices,'URL','https://www.sse.com.cn'),
            ('h1_159920',cn,'adjunctUrl','https://static.cninfo.com.cn/')]:
        if sum(base_url+r[url_key] == items[key][1]['url'] for r in catalog) != 1:
            raise ValueError('Report URL not uniquely identified in fund catalog: '+key)
    titles = [r['TITLE'] for r in notices] + [r['announcementTitle'] for r in cn]
    if any(re.search('分红|收益分配|折算|分拆|拆分|份额合并|拆细|份额调整', t) for t in titles):
        raise ValueError('Fund distribution or conversion notice requires review')
    if any(re.search('停牌|停复牌|复牌', r['announcementTitle']) for r in cn):
        raise ValueError('New opening restriction requires review')
    halts = set()
    for r in notices:
        day = date.fromisoformat(r['SSEDATE'])
        if START <= day <= END and re.search('停牌|停复牌|复牌', r['TITLE']):
            key = 'halt_' + day.strftime('%Y%m%d')
            path = source(items, key)
            content = ''.join(''.join(p.extract_text() for p in PdfReader(path).pages).split())
            if items[key][1]['url'] != 'https://www.sse.com.cn' + r['URL'] or (
                    f'{day.year}年{day.month}月{day.day}日开市起' not in content):
                raise ValueError('Opening restriction not matched: ' + key)
            halts.add((day, '513500'))
    return domestic, dates, bars, halts
