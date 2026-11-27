"""Offline research estimate from official cleared ETF units and same-date manager NAVs."""
import argparse
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.admission import catalog_rows, sessions_between
from etf_research.publication import create, verify_bundle

SNAP = ROOT/'data/snapshots/20261127T1605-official-etf-flow'
SEAL = 'd7b9fccb9dc451646d62c61387803405e751c88b16aec7bf2a27231b1bae4b2c'
REPORT = ROOT/'reports/2026-11-27-policy-pilot/etf-flow.json'
SYMBOLS = ('510300', '511010')
CONVERSION_DATES = {'510300':'2012年5月11日', '511010':'2013年3月5日'}
CONVERSION_TITLES = re.compile('折算|拆分|拆细|份额合并|份额调整|分拆')
SHARES_QUERY = 'COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L'
D = Decimal


def body(key):
    return (SNAP/(key+'.body')).read_bytes()


def read_sources():
    if hashlib.sha256((SNAP/'manifest.json').read_bytes()).hexdigest() != SEAL:
        raise ValueError('ETF flow snapshot manifest changed')
    verify_bundle(SNAP)
    sources = {}
    for r in json.loads((SNAP/'requests.json').read_bytes()):
        key = r['name']
        received, requested = (datetime.fromisoformat(r[k]) for k in ('received_at','requested_at_utc'))
        if (key in sources or r['status'] != 200 or r['curl_exit'] or r.get('error') or not r['bytes']
                or r['final_url'] != r['url'] or r['sha256'] != hashlib.sha256(body(key)).hexdigest()
                or not received.tzinfo or not requested.tzinfo or received < requested):
            raise ValueError('Unverified ETF flow source: '+key)
        sources[key] = dict(url=r['url'], snapshot=(SNAP/(key+'.body')).relative_to(ROOT).as_posix(),
                            sha256=r['sha256'], requestedAt=r['requested_at_utc'],
                            receivedAt=r['received_at'], publishedAt=None)
    return sources


def shares_for(day, sources):
    key = 'shares_'+day.strftime('%Y%m%d')
    u = urlsplit(sources[key]['url'])
    if u.netloc != 'query.sse.com.cn' or parse_qs(u.query).get('STAT_DATE') != [str(day)]:
        raise ValueError('Wrong Shanghai clearing date')
    data = json.loads(body(key))
    p, rows = data['pageHelp'], data['result']
    if (data['sqlId'] != SHARES_QUERY or data.get('actionErrors') or data.get('fieldErrors')
            or p['pageNo'] != 1 or p['pageCount'] != int(bool(rows)) or p['data'] != rows
            or p['total'] != len(rows) or any(r['STAT_DATE'] != str(day) for r in rows)
            or len({r['SEC_CODE'] for r in rows}) != len(rows)):
        raise ValueError('Incomplete or conflicting clearing table')
    result = {}
    for r in rows:
        if r['SEC_CODE'] in SYMBOLS:
            units = D(r['TOT_VOL'])*10000
            if not units.is_finite() or units <= 0 or units != units.to_integral_value():
                raise ValueError('Invalid cleared units')
            result[r['SEC_CODE']] = units
    return key, result, len(rows)


def manager_nav(sessions, sources):
    nav = {code:{} for code in SYMBOLS}
    hkey = 'nav_510300'
    u = urlsplit(sources[hkey]['url'])
    if (u.netloc != 'www.huatai-pb.com' or parse_qs(u.query).get('fundcode') != ['510300']
            or not u.path.endswith('/getFundNetTableJson')):
        raise ValueError('Wrong manager or series')
    data = json.loads(body(hkey)); rows = data['dataList']
    if data['totalPage'] != 1 or data['totalCount'] != len(rows) or data['currentPage'] != 1:
        raise ValueError('Incomplete Huatai NAV history')
    for r in rows:
        d, v = date.fromisoformat(r['date']), D(r['netvalue'])
        if (d not in sessions or d in nav['510300'] or r['fundcode'] != '510300'
                or r['netprecision'] != 4 or not v.is_finite() or v <= 0):
            raise ValueError('Wrong Huatai valuation identity')
        nav['510300'][d] = (v, hkey)
    for prev, effective in zip(sessions, sessions[1:]):
        stamp=effective.strftime('%Y%m%d')
        key='nav_511010_'+stamp
        xml=ET.fromstring(body(key))
        if (sources[key]['url']!='https://m.gtfund.com/cochin/etf/download/511010/'+stamp
                or xml.findtext('FundInstrumentID')!='511010' or xml.findtext('TradingDay')!=stamp
                or xml.findtext('PreTradingDay')!=prev.strftime('%Y%m%d')):
            raise ValueError('Guotai PCF valuation date or identity mismatch')
        v=D(xml.findtext('NAV'))
        basket=D(xml.findtext('NAVperCU')) / D(xml.findtext('CreationRedemptionUnit'))
        if not v.is_finite() or v <= 0 or abs(basket-v)>D('.0005'):
            raise ValueError('Guotai per-unit NAV differs from the creation basket')
        nav['511010'][prev]=(v,key)
    return nav


def conversion_basis(code, first, last, sources):
    key='catalog_'+code
    url=urlsplit(sources[key]['url'])
    q=parse_qs(url.query)
    if (url.netloc!='query.sse.com.cn' or q.get('SECURITY_CODE') != [code]
            or q.get('START_DATE') != ['2012-01-01'] or q.get('END_DATE') != [str(last)]):
        raise ValueError('Incomplete corporate action scope')
    notices=catalog_rows(json.loads(body(key)),code)
    effective=CONVERSION_DATES[code]
    matches=[(u,r) for u,r in notices.items() if CONVERSION_TITLES.search(r['TITLE'])]
    known = {'510300':{'2012-05-15'}, '511010':{'2013-02-27','2013-03-07'}}[code]
    if len(matches)!=len(known) or {r['SSEDATE'] for _,r in matches} != known:
        return False
    for name, literal in [('conversion_'+code,effective),('definition_'+code,'交易币种人民币')]:
        path=urlsplit(sources[name]['url']).path
        if path not in notices or notices[path]['SECURITY_CODE'] != code:
            raise ValueError('Unlinked corporate action or currency document')
        doc=PdfReader(SNAP/(name+'.body'))
        text=''.join(''.join(p.extract_text() or '' for p in doc.pages).split())
        if literal not in text or (name.startswith('conversion_') and '折算' not in text):
            raise ValueError('Corporate action or currency not confirmed')
    return all(date.fromisoformat(r['SSEDATE']) < first for _,r in matches)


def estimate(previous, current, *, comparable, adjacent, currency='CNY'):
    """Quantities are cleared units, prices are CNY per unit, never cumulative NAV."""
    q0,v0=previous
    q1,v1=current
    if not comparable or not adjacent or currency!='CNY' or any(
            x is None or not x.is_finite() or x<=0 for x in (q0,v0,q1,v1)):
        return None,None
    flow=(q1-q0)*v1
    return flow,flow/(q0*v0)


def number(x):
    return format(x,'f') if x is not None else None


def build(ready_at=None):
    sources=read_sources()
    periods=json.loads((ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json').read_bytes())
    sessions=sessions_between(periods['holiday_ranges'], date(2026,11,24),date(2026,11,27))
    shares={d:shares_for(d,sources) for d in sessions}
    nav=manager_nav(sessions,sources)
    rows=[]
    for code in SYMBOLS:
        comparable=conversion_basis(code,sessions[0],sessions[-1],sources)
        for prior,day in zip(sessions,sessions[1:]):
            k0,q0,_=shares[prior]; k1,q1,_=shares[day]
            q0,q1=q0.get(code),q1.get(code)
            v0,n0=nav[code].get(prior,(None,None)); v1,n1=nav[code].get(day,(None,None))
            flow,strength=estimate((q0,v0),(q1,v1),comparable=comparable,adjacent=True)
            keys=list(dict.fromkeys(k for k in (k0,k1,n0,n1,'catalog_'+code,'definition_'+code,'conversion_'+code) if k))
            received=max(sources[k]['receivedAt'] for k in keys)
            missing=[]
            if not comparable: missing.append('折算口径待核验')
            if q0 is None or q1 is None: missing.append('交易所当期或前期清算总份额尚缺')
            if v0 is None or v1 is None: missing.append('基金公司当期或前期单位净值尚缺')
            rows.append(dict(symbol=code,previousDate=str(prior),valuationDate=str(day),
                             previousShares=number(q0),totalShares=number(q1),sharesUnit='份',
                             previousUnitNav=number(v0),unitNav=number(v1),navUnit='人民币元/份',currency='CNY',
                             estimatedNetSubscriptionCny=number(flow),relativeIntensity=number(strength),
                             previousAssetsCny=number(q0*v0 if q0 is not None and v0 is not None else None),
                             buyerIdentity=None,status='unknown' if missing else 'verified_estimate',
                             reason='；'.join(missing) if missing else '相邻交易日、清算总份额、同估值日管理人单位净值及折算口径已核对。',
                             publishedAt=None,receivedAt=received,sourceKeys=keys))
    ready=ready_at or datetime.now(timezone.utc).isoformat()
    if datetime.fromisoformat(ready).tzinfo is None or any(
            datetime.fromisoformat(ready)<datetime.fromisoformat(s['receivedAt']) for s in sources.values()):
        raise ValueError('Feature ready time precedes source receipt')
    for row in rows:
        row['featureReadyAt']=ready if row['status']=='verified_estimate' else None
        row['availableAt']=row['featureReadyAt']
    return dict(schemaVersion=1,scope='国内两只ETF，人民币，清算后份额 × 当期单位净值',
                firstObservedCalculationAt=ready, rows=rows,sources=sources,
                unitsPrecision='上交所原表单位为万份，本样本目标证券披露到0.01万份。估算受原始舍入影响。',
                formula='(当期份额−上期份额)×当期单位净值，相对强度的分母为上期份额×上期单位净值。',
                timing='receivedAt 为组成该行的最迟实际收报时间。availableAt 采用全部核验结束时间，历史补采结果只在该时刻之后可查。精确首次公开时间未知。',
                clearingTableRows={str(d):n for d,(_,_,n) in shares.items()},
                navInterpretation='510300 取管理人单位净值字段。511010 取国泰PCF的NAV，估值日为PreTradingDay。',
                limitations='样本为日频净申购金额估算，证券持有人和实际现金交割、交易方向及市场影响均未知。四只ETF回测、前瞻模型和交易信号不读取此输出。')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--output',type=Path); g.add_argument('--verify',action='store_true')
    args=p.parse_args()
    if args.output:
        create(args.output,build())
    else:
        saved=json.loads(REPORT.read_bytes())
        if saved!=build(saved['firstObservedCalculationAt']):
            raise ValueError('Archived flow observations do not reproduce')
        print('ETF cleared-unit and NAV sample reproduced')
