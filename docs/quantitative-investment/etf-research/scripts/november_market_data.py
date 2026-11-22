"""Admit six closed sessions after the November 12 profile using sealed evidence."""
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
import hashlib
import json

import recent_market_data as prior
from etf_research.admission import completed_date, load_incremental, parse_prices, sessions_between
from etf_research.data import RawBar, verify_manifest
from etf_research.official_history import parse_dayk
from technical_factors import admit_volume

THROUGH = date(2026, 11, 20)
START = date(2026, 11, 13)
MARKET = '20261122-close-1120'
CONTROL = '20261122-cninfo-control'
DOMESTIC = '20261120T171001-76e9c947-prices'
SEALS = {MARKET:'bf23d29c81cf9e4bfafaa4b4b6b9a00dcb16b4d2dcf7926f27c360ffa6646c6e',
         CONTROL:'354c2bc5f4d058c634768ae2d14031d9caaf7c15aa734d983771fb6c43e45871',
         DOMESTIC:'620b64bc9f0b7dbf0a103e2ce4f2cff9133d9717195ae27a41f517c1b9088968'}


def evidence():
    for name, digest in SEALS.items():
        folder = prior.SNAPS/name
        if hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest() != digest:
            raise ValueError('Snapshot identity differs: '+name)
        verify_manifest(folder)
    root = prior.SNAPS/MARKET
    records = {}
    for record in json.loads((root/'requests.json').read_bytes()):
        name = record['name']
        path = root/(name+'.body')
        if (name in records or record['status'] != 200 or record['curl_exit'] or record.get('error')
                or record['url'] != record['final_url'] or completed_date(datetime.fromisoformat(record['requested_at_utc'])) < THROUGH
                or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']):
            raise ValueError('Invalid evidence: '+name)
        records[name] = path, record
    # Same stock, same query with a wider start and the new end: recover the two known filings.
    control = prior.SNAPS/CONTROL
    meta = json.loads((control/'request.json').read_bytes())
    cn = json.loads((control/'control.body').read_bytes())
    previous = json.loads((prior.SNAPS/prior.NOTICES/'cninfo_159920.body').read_bytes())
    base_query = records['cninfo_159920'][1]
    if (meta['status'] != 200 or meta['curl_exit'] or meta['url'] != base_query['url']
            or meta['post'] != base_query['post'].replace(str(START),'2026-10-26')
            or cn['hasMore'] or cn['totalAnnouncement'] != len(cn['announcements'])
            or {(r['secCode'],r['orgId'],r['adjunctUrl']) for r in cn['announcements']} !=
               {(r['secCode'],r['orgId'],r['adjunctUrl']) for r in previous['announcements']}):
        raise ValueError('CNINFO positive control differs')
    return records


@lru_cache(maxsize=1)
def admitted():
    (base, calendar, old_bars, old_halts), previous = prior.admitted()
    old_volume, _ = prior.volumes()
    records = evidence()
    halts, notices, count = prior.review_notices(records, START, THROUGH)
    cal = prior.SNAPS/'2026-11-04-calendar-08/calendar.json'
    days = sessions_between(json.loads(cal.read_bytes())['holiday_ranges'], START, THROUGH)
    domestic, _ = load_incremental(prior.SNAPS, DOMESTIC)
    if domestic.sessions[-len(days):] != days or domestic.dividends != tuple(
            e for e in base.dividends if e.record_date >= domestic.sessions[0]):
        raise ValueError('Domestic calendar or dividends changed')

    bars = {s:dict(b) for s,b in old_bars.items()}
    officials, sina_rows = {}, {}
    earlier_body = (prior.SNAPS/'20261120T104148-four-etf-quotes/quote_check.json').read_bytes()
    if hashlib.sha256(earlier_body).hexdigest() != '4ef30f705e714b52e1f02052bab8574ebcbf45e0493ba2fb541aab372efd9cc9':
        raise ValueError('November 19 quote audit changed')
    earlier = json.loads(earlier_body)['completedOHLC']
    for code, series in bars.items():
        exchange = 'sz' if code == '159920' else 'sh'
        expected = {
            'official': f'https://yunhq.sse.com.cn:32042/v1/{exchange}1/dayk/{code}?begin=0&end=-1&period=day',
            'sina': f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol={exchange}{code}&scale=240&ma=no&datalen=1970',
            'sohu': f'https://q.stock.sohu.com/hisHq?code=cn_{code}&start=20261102&end=20261120&stat=1&order=D&period=d&rt=json',
        }
        if any(records[p+'_'+code][1]['url'] != url for p,url in expected.items()):
            raise ValueError('Wrong quote source: '+code)

        path, _ = records['official_'+code]
        officials[code] = json.loads(path.read_bytes())
        official = {d:RawBar(d,**r) for d,r in parse_dayk(path.read_text(),code).items() if d <= THROUGH}
        sources = [official]
        for source in ('sina','sohu'):
            data = records[source+'_'+code][0].read_bytes()
            sources.append(parse_prices(data,source,THROUGH))
            if source == 'sina':
                text = data.decode()
                sina_rows[code] = json.loads(text[text.index('([')+1:text.rindex(')')])
        for prices in sources:
            if (prior.THROUGH not in prices or tuple(sorted(d for d in prices if d>prior.THROUGH)) != days
                    or any(prices[d] != series[d] for d in prices.keys() & series.keys())
                    or any(prices[d] != official[d] for d in days)):
                raise ValueError('Quote prefix, calendar or OHLC conflict: '+code)
        if code in domestic.bars and any(domestic.bars[code][d] != official[d] for d in days):
            raise ValueError('Domestic checkpoint price conflict')
        if any(getattr(official[d],k) != Decimal(earlier[code][str(d)][k])
               for d in days[:-1] for k in ('open','high','low','close')):
            raise ValueError('Previously sealed November quote differs')
        series.update({d:official[d] for d in days})
    shares, volume_audit = admit_volume((prior.THROUGH, *days),bars,officials,sina_rows)
    for code, values in shares.items():
        if values[prior.THROUGH] != old_volume[code][prior.THROUGH]:
            raise ValueError('Volume anchor changed')
    volumes = {s:{**v, **shares[s]} for s,v in old_volume.items()}
    merged = replace(base,sessions=base.sessions+days,bars={s:bars[s] for s in base.bars},
                     provenance=dict(base.provenance,end=str(THROUGH),session_count=len(base.sessions)+len(days)))
    audit = dict(through=str(THROUGH), priorThrough=str(prior.THROUGH), addedSessions=list(map(str,days)),
                 notices=notices, officialRegisterRows=count, openingHalts=sorted(str(d) for d,_ in halts),
                 volumeChecks=volume_audit, snapshotSeals=SEALS, unknown=previous['unknown'])
    return (merged,calendar+days,bars,old_halts|halts),audit,(volumes,volume_audit)
