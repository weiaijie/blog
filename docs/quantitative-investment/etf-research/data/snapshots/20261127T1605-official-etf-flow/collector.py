"""One-shot public-source capture for the November 24–27 ETF share/NAV pilot."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import sys

from etf_research.http_capture import HOSTS, fetch, load_policy, save_transport
from etf_research.publication import create, seal

ROOT = Path(sys.argv[1])
ROOT.mkdir(parents=True, exist_ok=False)
(ROOT/'collector.py').write_bytes(Path(__file__).read_bytes())
policy = load_policy()
save_transport(ROOT,policy)
HOSTS.update({'www.huatai-pb.com','m.gtfund.com'})
shares_api = 'https://query.sse.com.cn/commonQuery.do?'
jobs = {}
for date in ['2026-11-24','2026-11-25','2026-11-26','2026-11-27']:
    params = {'sqlId':'COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L','isPagination':'true','STAT_DATE':date,
              'pageHelp.pageSize':1500,'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.endPage':1,'pageHelp.cacheSize':1}
    jobs['shares_'+date.replace('-','')] = shares_api+urlencode(params)
for day in ('20261125','20261126','20261127'):
    jobs['nav_511010_'+day] = 'https://m.gtfund.com/cochin/etf/download/511010/'+day
jobs['nav_510300'] = 'https://www.huatai-pb.com/common-web/chart/fundnettable/getFundNetTableJson?fundcode=510300&from=2026-11-24&to=2026-11-27&pages=1-10&siteId=9496d23c648f4a72a79150c3f2ac669b'
jobs['definition_510300'] = 'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-11-24/510300_20261124_2XJH.pdf'
jobs['definition_511010'] = 'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-09-21/511010_20260921_SHP5.pdf'
jobs['conversion_510300'] = 'https://www.sse.com.cn/disclosure/fund/announcement/c/2012-05-15/510300_20120515_1.pdf'
jobs['conversion_511010'] = 'https://www.sse.com.cn/disclosure/fund/announcement/c/2013-03-06/511010_20130307_1.pdf'
for code in ('510300','511010'):
    params={'sqlId':'COMMON_PL_JJXX_JJGG_NEW_L','isPagination':'true','pageHelp.pageSize':1000,
            'pageHelp.pageNo':1,'pageHelp.beginPage':1,'pageHelp.endPage':1,'pageHelp.cacheSize':1,
            'SECURITY_CODE':code,'TITLE':'','START_DATE':'2012-01-01','END_DATE':'2026-11-27'}
    jobs['catalog_'+code]=shares_api+urlencode(params)
def grab(item):
    name,url=item
    row=fetch(ROOT,name,url,policy)
    row['received_at']=datetime.now(timezone.utc).isoformat()
    return row
with ThreadPoolExecutor(max_workers=4) as pool:
    requests=list(pool.map(grab,jobs.items()))
create(ROOT/'requests.json',requests)
seal(ROOT)
print([(r['name'],r['status'],r['bytes']) for r in requests])
