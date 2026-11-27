"""Offline admission of 2026-11-23, extending the separate November 20 dataset."""
from dataclasses import replace
from datetime import date, datetime, timedelta
from functools import lru_cache
import hashlib
import json
from urllib.parse import parse_qs, urlsplit

from audit_official_close import audit as domestic_close
from etf_research.admission import completed_date, load_incremental, parse_prices, sessions_between
from etf_research.data import RawBar, verify_manifest
from etf_research.official_history import parse_dayk
from market_evidence import SNAPS
import november_market_data as previous
from recent_market_data import NOTICES, review_notices
from technical_factors import admit_volume

THROUGH = date(2026, 11, 23)
START = previous.THROUGH + timedelta(days=1)
MARKET = '20261124T0910-close1123'
CONTROL = '20261124T0910-control1123'
DOMESTIC = '20261123T171001-e77ea484-prices'
OFFICIAL = '20261123T171001-e77ea484-official'
SEALS = {
    MARKET: 'efb47800caeb56f029cb17dfedda0f8db3c735a9b3125cd1215b34270dcdbb9a',
    CONTROL: '7667c8c2420cc4ed5df807dc341e08a8ae41ba8fd444117be4cb6b9cebcd6fb1',
    DOMESTIC: '9cdcaafdcddc609801e8036f4f74c3fb981b01c7964063068e5c960b80c7fe4e',
    OFFICIAL: 'b98bd3460cd92184ed2e789a35d7e145c0271cab66c9cf903c05ae37f29dcd73',
}


def extension_records(start, through, market, control_name, seals):
    for name, seal in seals.items():
        folder = SNAPS/name
        if hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest() != seal:
            raise ValueError('Snapshot identity differs: '+name)
        verify_manifest(folder)
    folder = SNAPS/market
    records = {}
    for record in json.loads((folder/'requests.json').read_bytes()):
        name = record['name']
        body = folder/(name+'.body')
        if (name in records or record['status'] != 200 or record['curl_exit'] or record.get('error')
                or record['url'] != record['final_url'] or completed_date(datetime.fromisoformat(record['requested_at_utc'])) < through
                or record['sha256'] != hashlib.sha256(body.read_bytes()).hexdigest()):
            raise ValueError('Unverified response: '+name)
        records[name] = body, record
    query = records['cninfo_159920'][1]
    control = SNAPS/control_name
    control_body = (control/'control.body').read_bytes()
    meta = json.loads((control/'request.json').read_bytes())
    result = json.loads(control_body)
    prior = json.loads((SNAPS/NOTICES/'cninfo_159920.body').read_bytes())
    def identities(rows):
        return {(r['secCode'], r['orgId'], r['announcementId'], r['adjunctUrl']) for r in rows}
    if (meta['status'] != 200 or meta['curl_exit'] or meta.get('error')
            or meta['url'] != query['url'] or meta['post'] != query['post'].replace(str(start)+'~', '2026-10-26~')
            or completed_date(datetime.fromisoformat(meta['requested_at_utc'])) < through
            or meta['sha256'] != hashlib.sha256(control_body).hexdigest()
            or result['hasMore'] or result['totalAnnouncement'] != len(result['announcements'])
            or not result['totalAnnouncement'] or identities(result['announcements']) != identities(prior['announcements'])):
        raise ValueError('CNINFO positive control changed')
    for name, code in [('register_all', ''), ('register_513500', '513500')]:
        params = parse_qs(urlsplit(records[name][1]['url']).query, keep_blank_values=True)
        if (params.get('startDate') != ['20261102'] or params.get('endDate') != [through.strftime('%Y%m%d')]
                or params.get('secCode') != [code]):
            raise ValueError('Wrong registration query scope: '+name)
    return records


def evidence():
    return extension_records(START, THROUGH, MARKET, CONTROL, SEALS)


def quote_extension(code, old, sessions, records, *, anchor=previous.THROUGH, through=THROUGH):
    market = 'sz' if code == '159920' else 'sh'
    urls = {
        'official': f'https://yunhq.sse.com.cn:32042/v1/{market}1/dayk/{code}?begin=0&end=-1&period=day',
        'sina': f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol={market}{code}&scale=240&ma=no&datalen=1970',
        'sohu': f'https://q.stock.sohu.com/hisHq?code=cn_{code}&start=20261102&end={through:%Y%m%d}&stat=1&order=D&period=d&rt=json',
    }
    sources, overlaps = {}, {}
    for name, url in urls.items():
        body, meta = records[name+'_'+code]
        if meta['url'] != url:
            raise ValueError('Wrong quote source: '+code)
        if name == 'official':
            raw = body.read_text(encoding='utf8')
            official = json.loads(raw)
            prices = {d: RawBar(d, **v) for d, v in parse_dayk(raw, code).items() if d <= through}
        else:
            raw = body.read_bytes()
            prices = parse_prices(raw, name, through)
            if name == 'sina':
                text = raw.decode()
                sina = json.loads(text[text.index('([')+1:text.rindex(')')])
        common = old.keys() & prices.keys()
        if (anchor not in common or any(old[d] != prices[d] for d in common)
                or tuple(sorted(d for d in prices if d > anchor)) != sessions):
            raise ValueError('Calendar or historical price changed: '+code+' '+name)
        overlaps[name] = len(common)
        sources[name] = prices
    added = {day: sources['official'][day] for day in sessions}
    if any(prices[d] != v for prices in sources.values() for d, v in added.items()):
        raise ValueError('New OHLC differs: '+code)
    return added, official, sina, overlaps


def extend(prior, through, records, domestic_snapshot, official_snapshot, seals):
    start = prior.THROUGH + timedelta(days=1)
    (base, calendar, old_bars, old_halts), prior_audit, (old_volume, _) = prior.admitted()
    halts, notices, register_count = review_notices(records, start, through)
    periods = json.loads((SNAPS/'2026-11-04-calendar-08/calendar.json').read_bytes())
    sessions = sessions_between(periods['holiday_ranges'], start, through)
    domestic, daily = load_incremental(SNAPS, domestic_snapshot)
    close = domestic_close(official_snapshot, domestic_snapshot, through)
    if (not sessions or sessions[-1] != through or domestic.sessions[-len(sessions):] != sessions
            or domestic.dividends != tuple(e for e in base.dividends if e.record_date >= domestic.sessions[0])):
        raise ValueError('Domestic session or dividend mismatch')

    bars, official, sina, overlaps = {}, {}, {}, {}
    for code, old in old_bars.items():
        added, official[code], sina[code], overlaps[code] = quote_extension(
            code, old, sessions, records, anchor=prior.THROUGH, through=through)
        if code in domestic.bars and any(domestic.bars[code][d] != v for d, v in added.items()):
            raise ValueError('Forward evidence disagrees with research prices: '+code)
        bars[code] = {**old, **added}
    shares, volume_audit = admit_volume((prior.THROUGH, *sessions), bars, official, sina)
    for code, values in shares.items():
        if values[prior.THROUGH] != old_volume[code][prior.THROUGH]:
            raise ValueError('Volume anchor differs: '+code)
    volume = {code: {**old_volume[code], **values} for code, values in shares.items()}
    merged = replace(base, sessions=base.sessions+sessions, bars={s:bars[s] for s in base.bars},
                     provenance=dict(base.provenance, end=str(through), session_count=len(base.sessions)+len(sessions)))
    audit = dict(through=str(through), priorThrough=str(prior.THROUGH), addedSessions=list(map(str, sessions)),
                 noticeWindowStart=str(start), notices=notices, officialRegisterRows=register_count,
                 openingHalts=sorted(str(d) for d, _ in halts), unchangedOverlap=overlaps,
                 cninfoPositiveControl=2, domesticCatalogCounts=daily['official_catalog_counts'],
                 domesticCloseManifest=close['source_manifest_sha256'], volumeChecks=volume_audit,
                 snapshotSeals=seals, unknown=prior_audit['unknown'])
    return (merged, calendar+sessions, bars, old_halts|halts), audit, (volume, volume_audit)

@lru_cache(maxsize=1)
def admitted():
    return extend(previous, THROUGH, evidence(), DOMESTIC, OFFICIAL, SEALS)
