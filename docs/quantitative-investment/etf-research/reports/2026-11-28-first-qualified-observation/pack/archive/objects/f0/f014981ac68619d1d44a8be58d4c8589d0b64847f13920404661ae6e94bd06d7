"""Collect a retrospective Shanghai margin/turnover sample into a new immutable snapshot."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
import sys
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.admission import sessions_between
from etf_research.http_capture import fetch, load_policy
from etf_research.publication import read, create, seal, sha

START, END = date(2026, 10, 20), date(2026, 11, 26)
CALENDAR = ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json'
RULE = 'https://www.sse.com.cn/lawandrules/guide/stock/jyglywznylc/zn/c/10830435/files/efee43e6d2444a27b4e202c4ecb7c0ee.docx'
MARGIN = 'https://www.sse.com.cn/market/othersdata/margin/sum/'
MARKET = 'https://www.sse.com.cn/market/view/'
HOST = 'https://query.sse.com.cn/'
PAGE_SIZE = 1500


def days():
    if sha(CALENDAR) != '950a3bfe2bab7ad484abc03aa27207bc70a49a4a144f495899cf1bd2aa10c8c6':
        raise ValueError('Calendar evidence changed')
    return sessions_between(read(CALENDAR)['holiday_ranges'], START, END)


def query(sql, start, end, page=1):
    summary = sql == 'RZRQ_HZ_INFO'
    params = {'sqlId':sql, 'beginDate':start.strftime('%Y%m%d'), 'endDate':end.strftime('%Y%m%d'),
              'isPagination':'true', 'pageHelp.pageSize':100 if summary else PAGE_SIZE, 'pageHelp.pageNo':page}
    return HOST+'commonSoaQuery.do?'+urlencode(params)


def jobs():
    yield 'margin_rules', MARGIN
    yield 'market_units', 'https://www.sse.com.cn/xhtml/home/2021public/querySearch/search_marketGeneralPicture.js'
    yield 'code_allocation', RULE
    yield 'margin', query('RZRQ_HZ_INFO', START, END)
    yield 'next_margin_probe', query('RZRQ_HZ_INFO', date(2026,11,27), date(2026,11,27))
    for d in days():
        key = d.strftime('%Y%m%d')
        yield 'market_'+key, HOST+'commonQuery.do?'+urlencode(dict(sqlId='COMMON_SSE_SJ_SCGM_C', TRADE_DATE=d.isoformat(),isPagination='false'))
        for page in (1,2):
            yield f'detail_{key}_{page}', query('RZRQ_MX_INFO',d,d,page)


def collect():
    folder = ROOT/'data/snapshots'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-sse-market-state')
    folder.mkdir(exist_ok=False)
    policy = load_policy()
    def capture(job):
        name, url = job
        row = fetch(folder,name,url,policy)
        row['receivedAt'] = datetime.now(timezone.utc).isoformat()
        return row
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(capture,jobs()))
    create(folder/'requests.json',rows)
    seal(folder)
    print(folder.name, len(rows), flush=True)


if __name__=='__main__':
    collect()
