"""Read dated fund-manager NAVs and official RMB central parities from sealed responses."""
import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal as D
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from market_evidence import SNAPS, START, END
from etf_research.data import verify_manifest

PREFIX = '2026-11-08-nav-fx-0536'
SYMBOLS = ('513500', '159920')


def responses():
    records = {}
    for suffix in 'abcdefghi':
        folder = SNAPS / (PREFIX+suffix)
        verify_manifest(folder)
        for row in json.loads((folder/'requests.json').read_text()):
            key = row['name']
            body = (folder/(key+'.body')).read_bytes()
            if key in records or hashlib.sha256(body).hexdigest() != row['sha256']:
                raise ValueError('Response identity or checksum: '+key)
            records[key] = row, body
    return records


def read(records, name, url):
    meta, raw = records[name]
    if (meta['url'] != url or meta['effective_url'] != url or meta['status'] != 200
            or meta['exit_code'] or not raw):
        raise ValueError('Unusable source '+name)
    return raw.decode('utf-8-sig')


def put(series, day, value):
    if START <= day <= END:
        if day in series or not value.is_finite() or value <= 0:
            raise ValueError('Duplicated or invalid value '+str(day))
        series[day] = value


def compact_day(s):
    return datetime.strptime(s,'%Y%m%d').date()


def tables(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',text,re.S|re.I):
        yield [re.sub(r'<[^>]*>','',c).strip() for c in
               re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',row,re.S|re.I)]


def manager_nav(records):
    us, hk = {}, {}
    for year in range(2023,2027):
        url = f'https://www.bosera.com/fund/fundNetValue.json?netValueType=NETVALUEPER&fundCode=513500&startDate={year}0101&endDate={year}1231'
        payload = json.loads(read(records,'chart_'+str(year),url))
        if payload['retCode'] != '0' or payload['data']['title'] != '单位净值':
            raise ValueError('Expected Bosera unit NAV series')
        for row in payload['data']['resultList']:
            (stamp,value), = row.items()
            day = compact_day(stamp)
            if day.year != year:
                raise ValueError('Wrong Bosera year')
            put(us,day,D(value))
    for page in range(1,38):
        key = {1:'h_first',2:'h_second'}.get(page,f'amc_{page:02}')
        url = f'https://www.chinaamc.com.cn/product/fundLishijingzhi.do?fundcode=159920&beginDate=2023-10-30&endDate=2026-10-30&pageIndex={page}&pageSize=1000'
        html = read(records,key,url)
        if (f"currentPage = '{page}'" not in html or "totalPage = '37'" not in html
                or not re.search(r'name="fundcode"\s+value="159920"',html)):
            raise ValueError('Incorrect ChinaAMC fund/page')
        rows = list(tables(html))
        if not any(r[:3] == ['净值日期','单位净值','累计净值'] for r in rows):
            raise ValueError('Unexpected ChinaAMC columns')
        actual = [r for r in rows if r and re.fullmatch(r'\d{4}-\d\d-\d\d',r[0])]
        if len(actual) != 20 and page != 37:
            raise ValueError('Incomplete ChinaAMC page')
        for stamp,unit,*rest in actual:
            put(hk,date.fromisoformat(stamp),D(unit))
    return {'513500':us,'159920':hk}


def vendor_nav(records, code):
    t = read(records,'em_'+code,'https://fund.eastmoney.com/pingzhongdata/'+code+'.js')
    if not re.search(r'var fS_code\s*=\s*"'+code+'"',t):
        raise ValueError('Wrong fund in NAV history')
    values = json.loads(re.search(r'var Data_netWorthTrend\s*=\s*(\[.*?\]);',t)[1],parse_float=D)
    em, ths = {}, {}
    for r in values:
        stamp = datetime.fromtimestamp(r['x']/1000,ZoneInfo('Asia/Shanghai'))
        put(em,stamp.date(),D(r['y']))
    js = read(records,'ths_'+code,f'https://fund.10jqka.com.cn/{code}/json/jsondwjz.json')
    rows = json.loads(re.fullmatch(r'\s*var dwjz_'+code+r'\s*=\s*(\[.*\])\s*;?\s*',js,re.S)[1])
    for stamp,value in rows:
        put(ths,compact_day(stamp),D(value))
    return em, ths


def official_fx(records):
    url = 'https://www.safe.gov.cn/AppStructured/hlw/RMBQuery.do?startDate=2023-10-30&endDate=2026-10-30&queryYN=true'
    safe_text = read(records,'safe_full',url)
    safe = {s:{} for s in SYMBOLS}
    cols = None
    for row in tables(safe_text):
        if '美元' in row and '港元' in row:
            cols = row.index('美元'),row.index('港元')
        if row and re.fullmatch(r'\d{4}-\d\d-\d\d',row[0]):
            if not cols:
                raise ValueError('Missing FX headings')
            for s,i in zip(SYMBOLS,cols):
                put(safe[s],date.fromisoformat(row[0]),D(row[i])/100)
    central = {s:{} for s in SYMBOLS}
    for s,key,typeid in [('513500','pbc_xml','1'),('159920','pbc_other','4')]:
        url = 'https://wzdt.pbc.gov.cn/huilv/flex-xml/flex_xml_'+typeid+'.xml'
        xml = ElementTree.fromstring(read(records,key,url))
        for node in xml.findall('Temp'):
            if node.findtext('typeid') != typeid:
                raise ValueError('FX currency identity changed')
            day = date.fromisoformat(node.findtext('date'))
            if START <= day <= END:
                put(central[s],day,D(node.findtext('hlvalue')))
    return safe,central


def checked(primary, others):
    if primary is None:
        return None,'missing_primary'
    seen = [r for r in others if r is not None]
    if not seen:
        return None,'missing_crosscheck'
    if any(r != primary for r in seen):
        return None,'conflict'
    return primary,'matched'


def market_rows(records, days, bars):
    managers = manager_nav(records)
    safe,pbc = official_fx(records)
    rows = []
    for s in SYMBOLS:
        em,ths = vendor_nav(records,s)
        for d in days:
            manager,first,second = managers[s].get(d),em.get(d),ths.get(d)
            nav,nav_status = checked(manager,[first,second])
            fx,fx_status = checked(safe[s].get(d),[pbc[s].get(d)])
            close = bars[s][d].close
            rows.append(dict(date=d,symbol=s,close_cny=close,manager_nav=manager,eastmoney_nav=first,
                             ths_nav=second,nav_status=nav_status,nav_cny=nav,
                             premium_cny=close-nav if nav else None,
                             premium_pct=100*(close/nav-1) if nav else None,
                             currency='USD' if s=='513500' else 'HKD',safe_cny_per_fc=safe[s].get(d),
                             pbc_cny_per_fc=pbc[s].get(d),fx_status=fx_status,cny_per_fc=fx))
    return rows
