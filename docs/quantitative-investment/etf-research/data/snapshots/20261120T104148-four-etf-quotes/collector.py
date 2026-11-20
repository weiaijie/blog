"""Capture four RMB ETF quotes and verify completed-session OHLC against the previous profile."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
import json
import sys
from zoneinfo import ZoneInfo

from etf_research.admission import completed_date, parse_prices, sessions_between
from etf_research.data import RawBar, verify_manifest
from etf_research.http_capture import fetch, load_policy, save_transport
from etf_research.official_history import parse_dayk
from etf_research.publication import create, seal
from recent_market_data import admitted, SNAPS, THROUGH

now = datetime.now(ZoneInfo('Asia/Shanghai'))
calendar = SNAPS / '2026-11-04-calendar-08'
verify_manifest(calendar)
holidays = json.loads((calendar/'calendar.json').read_bytes())['holiday_ranges']
days = sessions_between(holidays, THROUGH + timedelta(days=1), completed_date(now))
end = days[-1]
out = Path(sys.argv[1]) / now.strftime('%Y%m%dT%H%M%S-four-etf-quotes')
out.mkdir(exist_ok=False)
policy = load_policy()
save_transport(out, policy)
(out/'collector.py').write_bytes(Path(__file__).read_bytes())
jobs = {}
for code in ('510300','511010','513500','159920'):
    market = 'sz' if code == '159920' else 'sh'
    jobs[code] = {
        'official': f'https://yunhq.sse.com.cn:32042/v1/{market}1/dayk/{code}?begin=0&end=-1&period=day',
        'sina': f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol={market}{code}&scale=240&ma=no&datalen=40',
        'sohu': f'https://q.stock.sohu.com/hisHq?code=cn_{code}&start=20261102&end={end:%Y%m%d}&stat=1&order=D&period=d&rt=json',
    }
with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(fetch,out,f'{provider}_{code}',url,policy)
               for code, urls in jobs.items() for provider,url in urls.items()]
    rows = [job.result() for job in futures]
create(out/'requests.json', rows)
meta = {r['name']:r for r in rows}
prior = admitted()[0][2]
prices, blocked = {}, {}
for code, urls in jobs.items():
    try:
        sources = {}
        for provider,url in urls.items():
            name = f'{provider}_{code}'
            r = meta[name]
            body = (out/(name+'.body')).read_bytes()
            if (r['status'] != 200 or r['curl_exit'] or r.get('error') or r['final_url'] != url
                    or r['sha256'] != sha256(body).hexdigest()):
                raise ValueError('Transport failed: ' + name)
            if provider == 'official':
                source = {d:RawBar(d, **v) for d,v in parse_dayk(body.decode(),code).items() if d <= end}
            else:
                source = parse_prices(body, provider, end)
            overlap = prior[code].keys() & source.keys()
            if THROUGH not in overlap or any(prior[code][d] != source[d] for d in overlap):
                raise ValueError('Historical overlap differs: ' + name)
            if tuple(sorted(d for d in source if d > THROUGH)) != tuple(days):
                raise ValueError('Session set differs: ' + name)
            sources[provider] = source
        for d in days:
            if len({src[d] for src in sources.values()}) != 1:
                raise ValueError('OHLC mismatch: ' + str(d))
        prices[code] = {str(d):{k:str(getattr(sources['official'][d],k)) for k in ('open','high','low','close')} for d in days}
    except (ValueError,KeyError,IndexError) as exc:
        blocked[code] = str(exc)
audit = dict(scope='closed_session_quotes_only', through=str(end), priorThrough=str(THROUGH), sessions=list(map(str,days)),
             completedOHLC=prices, blocked=blocked, backtestAdmitted=False,
             actualRequests=sum(row['actual_requests'] for row in rows))
create(out/'quote_check.json', audit)
seal(out)
verify_manifest(out)
print(out.name, json.dumps(audit))
