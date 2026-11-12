"""Offline, exact-date audit. Does not admit market data or change tradability."""
import argparse, json, sys
from pathlib import Path
from decimal import Decimal as D
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.publication import sha, read, create, verify_bundle
from etf_research.long_history import load_long_history
from etf_research.admission import catalog_rows
BASE = ROOT/'data/snapshots'
VENDOR = BASE/'2026-11-07-session-evidence-134049'
QUOTES = BASE/'2026-11-07-exdate-quotes-134352'


def captured(folder):
    verify_bundle(folder)
    result = {}
    for r in read(folder/'requests.json'):
        p = folder/(r['name']+'.body')
        if sha(p) != r['sha256'] or r['name'] in result:
            raise ValueError('Request/body mismatch')
        result[r['name']] = (r, p)
    return result


def audit():
    data = load_long_history(BASE)
    quotes, vendor = captured(QUOTES), captured(VENDOR)
    evidence = { (e['symbol'],e['ex_date']):e for e in data.provenance['event_sources'] }
    rows, activity, titles = [], {}, []
    for e in data.dividends:
        s, day = e.symbol, e.ex_date
        dt = day.strftime('%Y%m%d')
        prev = data.sessions[data.sessions.index(day)-1]
        before = data.bars[s][prev].close
        theoretical = before-e.per_share
        meta, body = quotes[f'snap_{s}_{dt}']
        origin = None
        reply_date = None
        if meta['status']==200 and not meta.get('error'):
            q = json.loads(body.read_bytes(), parse_float=D)
            if q['code'] != s:
                raise ValueError('Wrong exchange symbol')
            reply_date = str(q['date'])
            if reply_date == dt:
                # Further review a dated response, including field semantics; never auto-admit.
                raise ValueError('New exact-date exchange record: requires formal reference review')
        sm, sb = vendor[f'sohu_{s}_{dt}']
        proxy = prices_match = volume_positive = None
        if sm['status']==200 and not sm.get('error'):
            v = json.loads(sb.read_bytes().decode('gb18030'))[0]
            if v['code']!='cn_'+s or v['status']!=0 or len(v['hq'])!=1 or v['hq'][0][0]!=day.isoformat():
                raise ValueError('Wrong vendor row')
            r = v['hq'][0]
            bar = data.bars[s][day]
            prices_match = [D(r[j]) for j in (1,6,5,2)] == [bar.open, bar.high, bar.low, bar.close]
            proxy = D(r[2])-D(r[3])
            volume_positive = D(r[7])>0 and D(r[8])>0
        rows.append(dict(symbol=s, ex_date=str(day), record_date=str(e.record_date), pay_date=str(e.pay_date),
            per_share=str(e.per_share), previous_session=str(prev), previous_raw_close=str(before),
            formula_before_rounding=str(theoretical), vendor_implied_from_close_minus_change=str(proxy) if proxy is not None else None,
            vendor_minus_formula=str(proxy-theoretical) if proxy is not None else None,
            vendor_raw_ohlc_matches=prices_match, vendor_positive_volume_amount=volume_positive,
            official_reference=origin, exchange_returned_date=reply_date,
            status='wrong_session' if reply_date else 'exchange_response_unavailable',
            exchange_request=meta['url'], exchange_sha256=meta['sha256'], vendor_request=sm['url'],
            vendor_sha256=sm['sha256'], dividend_announcement=evidence[(s,str(day))]))
    for s in data.bars:
        x = read(BASE/'2026-11-05-costs-11'/('official_full_'+s+'.body'))
        official = {str(r[0]):r for r in x['kline']}
        raw = (BASE/'2026-11-04-expansion-07'/('sina_daily_'+s+'.body')).read_text()
        sina = {r['day']:r for r in json.loads(raw[raw.index('([')+1:raw.rindex(')')])}
        unknown = []
        for day in data.sessions:
            r = official[day.strftime('%Y%m%d')]
            if not (D(str(r[5]))>0 and D(str(r[6]))>0 and D(str(sina[str(day)]['volume']))>0):
                unknown.append(str(day))
        activity[s] = dict(sessions=len(data.sessions), both_positive=len(data.sessions)-len(unknown), unknown_dates=unknown,
            start=str(data.sessions[0]), end=str(data.sessions[-1]), verified_no_intraday_halt=None, actual_fill=None)
        catalog = catalog_rows(read(BASE/'2026-11-03-official-02'/(s+'_all_index.body')), s)
        for url, r in catalog.items():
            if str(data.sessions[0])<=r['SSEDATE']<=str(data.sessions[-1]) and any(k in r['TITLE'] for k in ('停牌','复牌','暂停交易','恢复交易','暂停上市')):
                titles.append(dict(symbol=s,date=r['SSEDATE'],title=r['TITLE'],url='https://www.sse.com.cn'+url,
                    classification='underlying_stock_valuation' if '所持停牌股票' in r['TITLE'] and '估值' in r['TITLE'] else 'requires_review'))
    return dict(scope='Research-only bounded audit; positive turnover cannot locate intraday halts or prove fills. Unmodified engine.', events=rows,
        activity=activity, announcement_title_hits=titles, complete_halt_register=None,
        source_manifests={p.name:sha(p/'manifest.json') for p in (VENDOR,QUOTES,BASE/'2026-11-05-costs-11',BASE/'2026-11-04-expansion-07',BASE/'2026-11-03-official-02',BASE/'2026-11-06-suspension-15')},
        official_product=vendor['historical_product'][0]['url'], interface_manual_status=quotes['interface_manual'][0]['status'])


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    create(a.output, audit())
