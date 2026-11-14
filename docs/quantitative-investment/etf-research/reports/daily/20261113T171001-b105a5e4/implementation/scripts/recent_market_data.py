"""Sealed retrospective extension. No network, active-pointer writes or inferred fills."""
from dataclasses import replace
from datetime import date, datetime, timedelta
from functools import lru_cache
import hashlib
import json
import re
from urllib.parse import parse_qs, urlsplit

from pypdf import PdfReader
from audit_suspensions import validate
from etf_research.admission import completed_date, load_incremental, parse_prices, sessions_between, catalog_rows
from etf_research.data import RawBar, verify_manifest
from etf_research.official_history import parse_dayk
from market_evidence import SNAPS, END

THROUGH = date(2026, 11, 12)
MARKET = '20261113T034000-recent-market'
NOTICES = '20261113T034200-recent-notices'
REGISTER = '20261113T034500-recent-register'
CN_PDF = '20261113T034500-recent-cninfo-pdf'
DOMESTIC = '20261112T171001-360e8f7b-prices'
SEALS = {
    MARKET: '5081b79d42bb6925bce0dde6e9a07051631e4fad9a27810cebc77fae99f37859',
    NOTICES: '63e63bed7ce3813dbf2fe0fac33a0a5c56eda63442cf95ea10f29eb8e8df437c',
    REGISTER: '5d40608a8153d649bc5bbc9a90732a969955501185c510091875fb32db9df382',
    CN_PDF: 'cb39f0b634fbdf86a38d06eb8d53e771a4668658de2e833030c89f76f9931f2d',
}


def checked_sources():
    records = {}
    for folder, seal in SEALS.items():
        root = SNAPS/folder
        if hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest() != seal:
            raise ValueError('Recent evidence seal changed: '+folder)
        hashes = verify_manifest(root)
        for row in json.loads((root/'requests.json').read_bytes()):
            key = row['name']
            path = root/(key+'.body')
            if (key in records or row['status'] != 200 or row.get('error')
                    or row.get('curl_exit', row.get('exit_code')) != 0
                    or row.get('final_url', row.get('effective_url')) != row['url']
                    or row['sha256'] != hashes[path.name] or not row['bytes']
                    or completed_date(datetime.fromisoformat(row['requested_at_utc'])) < THROUGH):
                raise ValueError('Invalid recent source: '+key)
            records[key] = path, row
    return records


def review_notices(records):
    def document(key, url):
        path, row = records[key]
        if row['url'] != url:
            raise ValueError('Unbound announcement URL')
        return ''.join(''.join(p.extract_text() for p in PdfReader(path).pages).split())

    source, meta = records['catalog_513500']
    query = parse_qs(urlsplit(meta['url']).query)
    if (query.get('SECURITY_CODE') != ['513500'] or query.get('START_DATE') != ['2026-10-26']
            or query.get('END_DATE') != [str(THROUGH)]):
        raise ValueError('Wrong recent SSE catalog scope')
    payload = json.loads(source.read_bytes())
    catalog_rows(payload, '513500')
    source, meta = records['cninfo_159920']
    query = parse_qs(meta['post'])
    cn = json.loads(source.read_bytes())
    if (meta['url'] != 'https://www.cninfo.com.cn/new/hisAnnouncement/query'
            or query.get('stock') != ['159920,jjjl0000031']
            or query.get('seDate') != ['2026-10-26~2026-11-12'] or query.get('pageNum') != ['1']
            or cn['hasMore'] or len(cn['announcements']) != cn['totalAnnouncement']
            or len({r['announcementId'] for r in cn['announcements']}) != cn['totalAnnouncement']):
        raise ValueError('Incomplete CNINFO scope/pagination')
    reviewed, halts = [], set()
    for i, row in enumerate(payload['result']):
        title, day = row['TITLE'], date.fromisoformat(row['SSEDATE'])
        key = f'notice_513500_{i:02}'
        text = document(key, 'https://www.sse.com.cn'+row['URL'])
        if '513500' not in text or not date(2026,10,26) <= day <= THROUGH:
            raise ValueError('Announcement identity/date conflict')
        if re.search('分红|收益分配|折算|分拆|拆分|份额合并|拆细|份额调整', title):
            raise ValueError('Unreviewed distribution or conversion')
        kind = None
        if '停复牌公告' in title:
            literal = f'{day.year}年{day.month}月{day.day}日'
            if literal+'开市起至当日10：30停牌' not in text or literal+'10：30复牌' not in text:
                raise ValueError('Unreviewed opening halt times')
            halts.add((day, '513500'))
            kind = 'opening_halt_until_10:30'
        elif '暂停申购业务公告' in title:
            if day != date(2026,11,4) or '暂停申购起始日2026年11月4日' not in text or '投资者仍可进行本基金的二级市场交易' not in text:
                raise ValueError('Unreviewed subscription restriction')
            kind = 'primary_subscription_suspended_secondary_trading_permitted'
        elif '溢价风险提示公告' in title:
            if '溢价风险' not in text:
                raise ValueError('Risk warning text mismatch')
            kind = 'premium_warning'
        elif '第3季度报告' in title:
            kind = 'quarterly_report'
        elif '新增华西证券为申购、赎回代办券商' in title:
            kind = 'authorized_participant_added'
        if kind is None:
            raise ValueError('Unclassified official notice: '+title)
        reviewed.append(dict(symbol='513500', date=str(day), title=title, kind=kind,
                             url=records[key][1]['url'], sha256=records[key][1]['sha256']))
    for i, row in enumerate(cn['announcements']):
        if row['secCode'] != '159920' or row['orgId'] != 'jjjl0000031':
            raise ValueError('Wrong Shenzhen fund identity')
        key = f'notice_159920_{i:02}'
        text = document(key, 'https://static.cninfo.com.cn/'+row['adjunctUrl'])
        title = row['announcementTitle']
        if '159920' not in text:
            raise ValueError('Wrong Shenzhen PDF identity')
        if '第3季度报告' in title:
            kind = 'quarterly_report'
        elif '新增申购赎回代办证券公司' in title:
            kind = 'authorized_participant_added'
        else:
            raise ValueError('Unreviewed Shenzhen notice')
        reviewed.append(dict(symbol='159920', date=row['adjunctUrl'].split('/')[1], title=title, kind=kind,
                             url=records[key][1]['url'], sha256=records[key][1]['sha256']))
    for code, expected in [('513500', {'2022-03-29'}), ('159920', {'2018-06-22','2018-06-26'})]:
        path, meta = records['distribution_'+code]
        vendor = path.read_text().split('权益登记日')[-1].split('分红送配公告')[0]
        if meta['url'] != f'https://fundf10.eastmoney.com/fhsp_{code}.html' or set(re.findall(r'\d{4}-\d\d-\d\d',vendor)) != expected:
            raise ValueError('Distribution/split table changed')
    all_path, all_meta = records['register_all']
    all_rows, count = validate(all_meta, all_path.read_bytes())
    path, meta = records['register_513500']
    selected, _ = validate(meta, path.read_bytes())
    if selected != [r for r in all_rows if r['secCode'] == '513500']:
        raise ValueError('All-security and targeted suspension query differ')
    expected = {(date.fromisoformat(r['startStopDate'][:4]+'-'+r['startStopDate'][4:6]+'-'+r['startStopDate'][6:]),'513500') for r in selected}
    if (expected != halts or len(selected) != len(halts)
            or any(r['startStopDate'] != r['endStopDate'] or r['startStopType'] != 'LSTP' or r['stopTime'] != '915' for r in selected)
            or any(r['secCode'] in ('510300','511010') for r in all_rows)):
        raise ValueError('Official halt registers and PDF review disagree')
    return halts, reviewed, count


@lru_cache(maxsize=1)
def admitted():
    from interactive_backtest import frozen_inputs
    base, calendar, prior, old_halts = frozen_inputs()
    records = checked_sources()
    halts, reviewed, registered = review_notices(records)
    domestic, domestic_audit = load_incremental(SNAPS, DOMESTIC)
    if domestic.sessions[-1] != THROUGH or domestic.dividends != base.dividends:
        # The short domestic loader omits earlier dividends: compare the shared interval below.
        if domestic.sessions[-1] != THROUGH or domestic.dividends != tuple(e for e in base.dividends if e.record_date >= domestic.sessions[0]):
            raise ValueError('Domestic endpoint/events require review')
    verify_manifest(SNAPS/'2026-11-04-calendar-08')
    ranges = json.loads((SNAPS/'2026-11-04-calendar-08/calendar.json').read_bytes())['holiday_ranges']
    added = sessions_between(ranges, END+timedelta(days=1), THROUGH)
    bars, checks = {s:dict(v) for s,v in prior.items()}, {}
    for code in bars:
        market = 'sz' if code == '159920' else 'sh'
        path, meta = records['official_'+code]
        if meta['url'] != f'https://yunhq.sse.com.cn:32042/v1/{market}1/dayk/{code}?begin=0&end=-1&period=day':
            raise ValueError('Wrong official quote identity')
        official = {d:RawBar(d,**v) for d,v in parse_dayk(path.read_text(),code).items() if d <= THROUGH}
        sources = {'official':official}
        for provider in ('sina','sohu'):
            path, meta = records[provider+'_'+code]
            expected = (f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol={market}{code}&scale=240&ma=no&datalen=1970' if provider=='sina' else f'https://q.stock.sohu.com/hisHq?code=cn_{code}&start=20261026&end=20261112&stat=1&order=D&period=d&rt=json')
            if meta['url'] != expected:
                raise ValueError('Wrong quote provider identity')
            sources[provider] = parse_prices(path.read_bytes(),provider,THROUGH)
        overlaps = {}
        for provider, prices in sources.items():
            common = prices.keys() & prior[code].keys()
            if END not in common or any(prices[d] != prior[code][d] for d in common):
                raise ValueError('Historical quote revision: '+code+'/'+provider)
            if tuple(d for d in sorted(prices) if END < d <= THROUGH) != added:
                raise ValueError('Missing recent calendar session: '+code+'/'+provider)
            overlaps[provider] = len(common)
        for d in added:
            if any(p[d] != official[d] for p in sources.values()):
                raise ValueError('Recent OHLC conflict: '+code)
            if code in domestic.bars and official[d] != domestic.bars[code][d]:
                raise ValueError('Domestic admitted dataset differs')
            bars[code][d] = official[d]
        checks[code] = dict(newDays=len(added), unchangedOverlap=overlaps, exactFieldsPerProvider=4*len(added))
    if any((d,s) not in old_halts for d,s in halts if d<=END):
        raise ValueError('Historical execution restriction changed')
    merged = replace(base, sessions=base.sessions+added, bars={s:bars[s] for s in base.bars},
                     provenance=dict(base.provenance,end=str(THROUGH),session_count=len(base.sessions)+len(added),recent_manifest_seals=SEALS))
    audit = dict(through=str(THROUGH), addedSessions=list(map(str,added)), sourceChecks=checks,
                 notices=reviewed, officialRegisterRows=registered,
                 openingHalts=[str(d) for d,s in sorted(halts) if d>END],
                 domesticAdmission=domestic_audit, snapshotSeals=SEALS,
                 executionRule='Opening halt blocks the scheduled opening order; no synthetic 10:30 fill or automatic catch-up.',
                 unknown=['独立停复牌完整性（尤其深市）仍未知；目录无记录不是从未停牌证明。',
                          '公告精确首次发布时间、临停后真实成交价/可成交量未知。',
                          '近期同步IOPV、净值/外汇与折溢价未在本轮完成核验，不用于交易因子。',
                          '13次分红的部分正式除息参考价缺口保留；本轮没有新增分红事件。'],
                 retrospective=True, changesForwardAccount=False)
    return (merged, calendar+added, bars, old_halts|halts), audit


def inputs():
    return admitted()[0]


@lru_cache(maxsize=1)
def volumes():
    from research_profile import using, FROZEN
    from technical_factors import volume_inputs, admit_volume
    with using(FROZEN):
        old, old_audit = volume_inputs()
    base, _, bars, _ = inputs()
    records = checked_sources()
    official, sina = {}, {}
    for symbol in old:
        official[symbol] = json.loads(records['official_'+symbol][0].read_bytes())
        text = records['sina_'+symbol][0].read_text()
        sina[symbol] = json.loads(text[text.index('([')+1:text.rindex(')')])
    first = max(date.fromisoformat(rows[0]['day']) for rows in sina.values())
    days = tuple(d for d in base.sessions if d>=first)
    checked, audit = admit_volume(days,bars,official,sina)
    merged = {s:dict(v) for s,v in old.items()}
    for s, values in checked.items():
        if any(old[s][d] != v for d,v in values.items() if d in old[s]):
            raise ValueError('Previously admitted volume revision')
        merged[s].update(values)
        if set(merged[s]) != set(base.sessions):
            raise ValueError('Incomplete extended volume series')
    return merged, dict(symbols=audit, prior=old_audit, snapshot=MARKET,
                        limitations='Relative volume only; free float and real executable capacity remain unknown.')
