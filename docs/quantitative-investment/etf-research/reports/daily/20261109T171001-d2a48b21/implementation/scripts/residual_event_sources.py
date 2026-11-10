"""Point-in-time evidence for historical 513500 creation limits and public warnings."""
import hashlib
import json
import re
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile
from zoneinfo import ZoneInfo

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT/'data/snapshots'
NEW = '2026-11-08-residual-events-0712'
OLD = '2026-11-08-close-timing-0603'
MARKET = '2026-11-08-markets-051007'
ZONE = ZoneInfo('Asia/Shanghai')


def checked(folder, name):
    directory = SNAP / folder
    raw = (directory / name).read_bytes()
    hashes = json.loads((directory/'manifest.json').read_bytes())
    if hashlib.sha256(raw).hexdigest() != hashes[name]:
        raise ValueError('Incorrect snapshot hash: ' + name)
    return raw


def offerings(dates, observations):
    records = {}
    metadata = {r['day']:r for r in json.loads(checked(OLD+'i','requests.json'))}
    with ZipFile(SNAP/(OLD+'i')/'responses.zip') as archive:
        for day in dates:
            stamp = day.replace('-','')
            suffix, filename = ('a','pcf_example.body') if stamp == '20250228' else ('b','pcf_'+stamp+'.body')
            page = checked(OLD+suffix,filename).decode('utf8')
            cells = dict(re.findall(r'<th>([^<]+)</th>\s*<td>([^<]+)</td>', page))
            flags = tuple(cells['是否允许'+label].strip() for label in ('申购','赎回'))
            if any(flag not in ('是','否') for flag in flags):
                raise ValueError('Unknown PCF permission')
            official = archive.read(stamp+'.body')
            if hashlib.sha256(official).hexdigest()!=metadata[stamp]['sha256']:
                raise ValueError('PCF file hash mismatch')
            fields = dict(line.split('=',1) for line in official.split(b'TAGTAG')[0].decode('gb18030').splitlines() if '=' in line)
            expected = {('是','是'):'1',('否','否'):'0',('否','是'):'3'}
            if (fields['Fundid1'], fields['TradingDay'], fields['CreationRedemption']) != ('513500',stamp,expected[flags]):
                raise ValueError('Inconsistent PCF identity or flags ' + day)
            cutoff = datetime.combine(date.fromisoformat(day),time(15),ZONE)
            if not datetime.fromisoformat(observations[day]['pcf_last_modified']) <= cutoff:
                raise ValueError('PCF file postdates cutoff')
            cap = int(Decimal(cells['当日累计申购份额上限(单位：份)'].replace(',','')))
            records[day] = dict(creation=flags[0],redemption=flags[1],listed_cap=cap,
                                effective_cap=cap if flags[0]=='是' else 0,
                                pcf_source=f'data/snapshots/{OLD+suffix}/{filename}')
    return records


def outstanding(dates):
    result = {}
    for day in dates:
        folder = NEW + ('m' if day == '2024-12-18' else 'n')
        raw = checked(folder, 'shares_'+day.replace('-','')+'.body')
        data = json.loads(raw)
        page = data['pageHelp']
        if (data['sqlId'] != 'COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L' or
                page['total'] != len(page['data']) or any(r['STAT_DATE']!=day for r in page['data'])):
            raise ValueError('Incomplete or misdated exchange share table')
        row, = [r for r in page['data'] if r['SEC_CODE']=='513500' and r['ETF_TYPE']=='跨境']
        result[day] = Decimal(row['TOT_VOL'])*10000
    return result


# Checked against each signed ETF notice, including explicit holiday expiry.
EVENTS = {
    '513500_20241217_PJRH.pdf': ('2024-12-17','2024-12-17','secondary_halt',
                                '开市起至当日10：30停牌','10：30复牌'),
    '513500_20241224_3QN8.pdf': ('2024-12-25','2024-12-25','both_closed',
                                '12月25日暂停本基金的申购、赎回','12月26日起恢复'),
    '513500_20250108_7ZVR.pdf': ('2025-01-09','2025-01-09','both_closed',
                                '1月9日暂停本基金的申购、赎回','1月10日起恢复'),
    '513500_20250110_8M4Q.pdf': ('2025-01-10','2025-02-18','creation_closed',
                                '暂停申购起始日2025年1月10日','仍可进行本基金的二级市场交易'),
    '513500_20250117_4V7V.pdf': ('2025-01-20','2025-01-20','redemption_closed',
                                '1月20日暂停本基金的赎回','1月21日起恢复'),
    '513500_20250214_U2GK.pdf': ('2025-02-17','2025-02-17','redemption_closed',
                                '2月17日暂停本基金的赎回','2月18日起恢复'),
    '513500_20250219_GG1C.pdf': ('2025-02-19','2025-04-07','creation_reopened',
                                '自2025年2月19日起','恢复办理申购业务'),
}


def issuer_entries():
    rows = []
    for n in (1,2):
        page=json.loads(checked(NEW+'f',f'bosera_p{n}.body'))['data']
        if page['fundCode']!='513500' or page['paginator']['page']!=n:
            raise ValueError('Wrong issuer catalog')
        rows.extend(page['resultList'])
    if len(rows)!=page['paginator']['totalRecord'] or len({r['id'] for r in rows})!=len(rows):
        raise ValueError('Incomplete issuer catalog')
    by_url={'https://www.bosera.com'+r['url']:r for r in rows}
    for req in json.loads(checked(NEW+'h','requests.json')):
        detail=checked(NEW+'h',req['name']+'.body').decode()
        row=by_url[req['url']]
        if (req['status']!=200 or '<h2>'+row['title']+'</h2>' not in detail or
                '时间：'+row['originalTime']+' 00:00:00' not in detail):
            raise ValueError('Issuer page identity or time evidence changed')
    return rows


def catalog():
    raw = json.loads(checked(MARKET,'sse_catalog.body'))
    page = raw['pageHelp']
    if len(page['data'])!=page['total']:
        raise ValueError('Incomplete announcement catalog')
    files = {}
    for folder in (NEW+'a', OLD+'e', MARKET+'c'):
        for r in json.loads(checked(folder,'requests.json')):
            if r['url'].lower().endswith('.pdf') and r['status']==200 and not r['exit_code']:
                files[r['url']] = (folder,r['name']+'.body')
    notices = []
    for r in page['data']:
        day,title = r['SSEDATE'],r['TITLE']
        if not ('2024-11-20'<=day<='2025-04-07' and
                any(k in title for k in ('停牌','停复牌','溢价','暂停','恢复申购','恢复赎回'))):
            continue
        url = 'https://www.sse.com.cn'+r['URL']
        folder, name = files[url]
        raw = checked(folder,name)
        if not raw.startswith(b'%PDF') or r['SECURITY_CODE']!='513500':
            raise ValueError('Unexpected notice source')
        reader = PdfReader(SNAP/folder/name)
        text = re.sub(r'\s+','',''.join(p.extract_text() for p in reader.pages))
        if '513500' not in text or '博时' not in text:
            raise ValueError('Unbound notice ' + name)
        signature = re.search(r'博时基金管理有限公司(20\d\d)年(\d{1,2})月(\d{1,2})日[。\d]*$',text)
        signed = date(*map(int,signature.groups())).isoformat() if signature else None
        event=EVENTS.get(Path(url).name)
        if event and not all(phrase in text for phrase in event[3:]):
            raise ValueError('Effective-date evidence changed: '+url)
        notices.append(dict(effect_from=event[0] if event else None,effect_through=event[1] if event else None,
                            event=event[2] if event else None,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                            catalog_date=day,signed_date=signed,title=title,url=url,
                            source=f'data/snapshots/{folder}/{name}',risk='溢价' in title,
                            conditional_halt=('申请' in text and '停牌' in text and '若' in text),
                            pdf_created=reader.metadata.creation_date,first_publication=None))
    if len([n for n in notices if n['event']])!=len(EVENTS):
        raise ValueError('Missing scheduled event')
    return sorted(notices,key=lambda r:(r['catalog_date'],r['url']))


def halt_registry():
    raw=json.loads(checked(NEW+'a','sse_halts.body'))
    page=raw['pageHelp']
    if (raw['sqlId']!='SSE_PL_JYTS_TFPXX_JJ' or page['total']!=len(page['data']) or
            page['data']!=raw['result'] or any(r['secCode']!='513500' for r in page['data'])):
        raise ValueError('Invalid halt registry')
    return {datetime.strptime(r['startStopDate'],'%Y%m%d').date().isoformat():r for r in page['data']}


def press_by_day():
    issues, copies = {}, {}
    for r in json.loads(checked(NEW+'r','press.json')):
        if not r['title_and_code_present'] or r['status']!=200:
            raise ValueError('Unbound press evidence')
        if r['name'].startswith('article_'):
            day=datetime.strptime(r['name'].removeprefix('article_'),'%Y%m%d').date().isoformat()
            issues[day]=r
        else:
            clock=datetime.fromisoformat(r['publisher_clock'])
            if clock.tzinfo is None:
                clock=clock.replace(tzinfo=ZONE)
            day=clock.astimezone(ZONE).date().isoformat()
            if clock.astimezone(ZONE).time()<=time(15):
                copies[day]=(clock.isoformat(),r)
    return issues,copies
