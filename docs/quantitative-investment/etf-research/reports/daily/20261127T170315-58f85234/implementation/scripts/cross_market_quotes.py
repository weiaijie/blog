"""Verified, display-only RMB quotes following the frozen backtest sample."""
from datetime import date, datetime, timedelta
import hashlib
import json

from etf_research.admission import completed_date, parse_prices, sessions_between
from etf_research.data import RawBar, verify_manifest
from etf_research.official_history import parse_dayk
from market_evidence import END, SNAPS

THROUGH = date(2026, 11, 9)
SNAPSHOT = '20261110T135427-cross-quotes-2BVjXn73'


def checked_extension(sources, prior, days):
    for name, bars in sources.items():
        if END not in bars or any(bars[d] != prior[d] for d in bars.keys() & prior.keys()):
            raise ValueError('Historical quote anchor or overlap differs: '+name)
        if tuple(sorted(d for d in bars if END < d <= THROUGH)) != days:
            raise ValueError('Missing or extra quote date: '+name)
    reference = sources['official']
    if any(bars[d] != reference[d] for bars in sources.values() for d in days):
        raise ValueError('Cross-market OHLC disagreement')
    return {d:reference[d] for d in days}


def cross_quotes(prior, holidays):
    folder = SNAPS/SNAPSHOT
    verify_manifest(folder)
    rows = json.loads((folder/'requests.json').read_bytes())
    records = {r['name']:r for r in rows}
    days = sessions_between(holidays, END+timedelta(days=1), THROUGH)
    result = {}
    for code, market in [('513500','sh'),('159920','sz')]:
        urls = {
            'official':f'https://yunhq.sse.com.cn:32042/v1/{market}1/dayk/{code}?begin=0&end=-1&period=day',
            'sina':f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol={market}{code}&scale=240&ma=no&datalen=40',
            'sohu':f'https://q.stock.sohu.com/hisHq?code=cn_{code}&start=20261026&end=20261109&stat=1&order=D&period=d&rt=json'}
        sources = {}
        for provider,url in urls.items():
            name = provider+'_'+code
            r = records[name]
            body = (folder/(name+'.body')).read_bytes()
            if (len(records)!=len(rows) or r['status']!=200 or r['curl_exit'] or r.get('error')
                    or r['url']!=url or r['final_url']!=url or hashlib.sha256(body).hexdigest()!=r['sha256']
                    or completed_date(datetime.fromisoformat(r['requested_at_utc'])) < THROUGH):
                raise ValueError('Unverified quote source: '+name)
            if provider == 'official':
                sources[provider] = {d:RawBar(d,**v) for d,v in parse_dayk(body.decode(),code).items()}
            else:
                sources[provider] = parse_prices(body,provider,THROUGH)
        result[code] = checked_extension(sources,prior[code],days)
    return result
