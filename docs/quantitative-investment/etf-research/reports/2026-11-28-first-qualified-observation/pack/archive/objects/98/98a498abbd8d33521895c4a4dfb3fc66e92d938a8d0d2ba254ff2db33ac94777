"""Build or verify the dated SSE pilot. All decisions remain outside the trading engine."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile
import re

from collect_market_state_pilot import ROOT, END, MARKET, MARGIN, RULE, PAGE_SIZE, days, jobs
from etf_research.admission import completed_date
from etf_research.publication import create, read, sha, verify_bundle

SNAPSHOT = '20261127T080707Z-sse-market-state'
SEAL = '6d495446303a0eb9eb71c9e86b76c840747d6de3f874e15a3583f07ca5d19c8c'
REPORT = ROOT/'reports/2026-11-27-policy-pilot/market-state.json'
CODES = {'600','601','603','605','688','689'}
BOARDS = ('主板A', '科创板')
HUNDRED_MILLION = Decimal(100000000)


def sources(snapshot):
    if sha(snapshot/'manifest.json') != SEAL:
        raise ValueError('Unexpected capture manifest')
    verify_bundle(snapshot)
    expected = dict(jobs())
    records = read(snapshot/'requests.json')
    if len(records)!=len(expected) or {r['name'] for r in records}!=expected.keys():
        raise ValueError('Unexpected request inventory')
    received = []
    for r in records:
        p = snapshot/(r['name']+'.body')
        t = datetime.fromisoformat(r['receivedAt'])
        started = datetime.fromisoformat(r['requested_at_utc'])
        if (r['url']!=expected[r['name']] or r['url']!=r['final_url'] or r['status']!=200
                or r['curl_exit'] or r.get('error') or r['metrics']['ssl_verify_result']!=0
                or r['sha256']!=sha(p) or r['bytes']!=p.stat().st_size
                or t.tzinfo is None or started.tzinfo is None or t<started or completed_date(started)<END):
            raise ValueError('Evidence mismatch: '+r['name'])
        received.append(t)
    with ZipFile(snapshot/'code_allocation.body') as source:
        xml = ElementTree.fromstring(source.read('word/document.xml'))
    coded = set()
    for tr in xml.findall('.//{*}tr'):
        cells = [''.join(t.text or '' for t in td.findall('.//{*}t')).strip() for td in tr.findall('{*}tc')]
        if len(cells)>=4 and cells[0]=='6' and cells[2] in ('A股','存托凭证'):
            coded.add(cells[0]+cells[1])
    if coded!=CODES:
        raise ValueError('A-share / CDR code table changed')
    if '本日融资余额＝前日融资余额＋本日融资买入额－本日融资偿还额' not in (snapshot/'margin_rules.body').read_text('utf8'):
        raise ValueError('Shanghai margin equation changed')
    script = (snapshot/'market_units.body').read_text('utf8')
    if '成交额(亿元)' not in script or 'TOTAL_TRADE_AMT' not in script:
        raise ValueError('Turnover units changed')
    return max(received)


def result(snapshot,name,sql):
    obj=read(snapshot/(name+'.body'))
    if obj['sqlId']!=sql or any(obj[k] for k in ('fieldErrors','actionErrors','actionMessages')):
        raise ValueError('Wrong or rejected query: '+name)
    return obj


def amount(r,key):
    v=r[key]
    if type(v) is not int or v<0:
        raise ValueError('Expected nonnegative reported CNY: '+key)
    return v


def equation(current, previous):
    if previous is None:
        return dict(status='missing_previous',expectedBalanceCny=None,residualCny=None)
    expected=amount(previous,'rzye')+amount(current,'rzmre')-amount(current,'rzche')
    residual=amount(current,'rzye')-expected
    return dict(status='matched' if residual==0 else 'mismatch',
                expectedBalanceCny=str(expected),residualCny=str(residual))


def financing_detail(snapshot,key,page_count=2):
    rows=[]
    total=None
    for page in range(1,page_count+1):
        r=result(snapshot,f'detail_{key}_{page}','RZRQ_MX_INFO')
        pg=r['pageHelp']
        if (pg['pageNo']!=page or pg['pageCount']!=page_count or pg['pageSize']!=PAGE_SIZE
                or pg['data']!=r['result'] or (page<page_count and len(r['result'])!=PAGE_SIZE)
                or (total is not None and pg['total']!=total)):
            raise ValueError('Incomplete margin detail page '+key)
        rows.extend(r['result'])
        total=pg['total']
    codes=[x['stockCode'] for x in rows]
    if len(set(codes))!=total or len(rows)!=total or any(x['opDate']!=key for x in rows):
        raise ValueError('Duplicate, incomplete or wrong-date margin orders')
    if any(not re.fullmatch(r'[0-9]{6}',code) or (code[0]=='6' and code[:3] not in CODES) for code in codes):
        raise ValueError('Unclassified code')
    return rows


def turnover(snapshot,key):
    records=result(snapshot,'market_'+key,'COMMON_SSE_SJ_SCGM_C')['result']
    by_name={r['PRODUCT_NAME']:r for r in records}
    if len(records)!=len(by_name) or any(r['TRADE_DATE']!=key for r in records):
        raise ValueError('Ambiguous market date or product')
    units=[Decimal(by_name[board]['TOTAL_TRADE_AMT']) for board in BOARDS]
    if any(not v.is_finite() or v<=0 for v in units):
        raise ValueError('Invalid published turnover')
    return sum(units)*HUNDRED_MILLION


def prior_ratio(values, current):
    return current/(sum(values[-20:])/20) if len(values)>=20 else None


def build(ready_at=None, *, project=None):
    root = ROOT if project is None else project
    snapshot=root/'data/snapshots'/SNAPSHOT
    received=sources(snapshot)
    obj=result(snapshot,'margin','RZRQ_HZ_INFO')
    summary=obj['result']
    sums={r['opDate']:r for r in summary}
    schedule=[d.strftime('%Y%m%d') for d in days()]
    if (set(schedule)!=sums.keys() or obj['pageHelp']['total']!=len(sums) or len(summary)!=len(sums)
            or obj['pageHelp']['data']!=summary or obj['pageHelp']['pageCount']!=1):
        raise ValueError('Margin dates differ from exchange calendar')
    rows,turnovers=[],[]
    prev=prev_etf=None
    for key in schedule:
        m=sums[key]
        detail=financing_detail(snapshot,key)
        reported_buy=amount(m,'rzmre')
        detail_buy=sum(amount(r,'rzmre') for r in detail)
        if detail_buy!=reported_buy:
            raise ValueError('Published detail financing buys do not sum to Shanghai total: '+key)
        if amount(m,'rzye')+amount(m,'rqylje')!=amount(m,'rzrqjyzl'):
            raise ValueError('Financing plus short balance differs from combined balance: '+key)
        stocks=[r for r in detail if r['stockCode'][:3] in CODES]
        if not stocks:
            raise ValueError('Empty share universe')
        stock_buy=sum(amount(r,'rzmre') for r in stocks)
        value=turnover(snapshot,key)
        if stock_buy>value:
            raise ValueError('Financing buys exceed same-market turnover')
        rel=prior_ratio(turnovers,value)
        turnovers.append(value)
        etf=next(r for r in detail if r['stockCode']=='510300')
        identity=equation(m,prev)
        flow=reported_buy-amount(m,'rzche')
        date_text=datetime.strptime(key,'%Y%m%d').date().isoformat()
        rows.append(dict(date=date_text,financingBalanceCny=str(m['rzye']),financingBuyCny=str(reported_buy),
                         financingRepaymentCny=str(m['rzche']),financingNetCny=str(flow),
                         financingBalanceChangeCny=str(m['rzye']-prev['rzye']) if prev is not None else None,
                         balanceIdentity=identity,combinedMarginBalanceCny=str(m['rzrqjyzl']),
                         securitiesLendingBalanceCny=str(m['rqylje']),combinedBalanceMatched=True,
                         reconciledFinancingNetCny=str(flow) if identity['status']=='matched' else None,
                         stockFinancingBuyCny=str(stock_buy),turnoverCny=format(value,'f'),
                         financingBuyShare=str(Decimal(stock_buy)/value),
                         relativeTurnover20=str(rel) if rel is not None else None,
                         priorTurnoverSessions=min(20,len(turnovers)-1),
                         priorTurnoverMeanCny=str(sum(turnovers[-21:-1])/20) if rel is not None else None,
                         breadth=None,detailRows=len(detail),stockMarginDetailRows=len(stocks),
                         sample510300=dict(financingBalanceCny=str(etf['rzye']),financingBuyCny=str(etf['rzmre']),
                                           financingRepaymentCny=str(etf['rzche']),balanceIdentity=equation(etf,prev_etf)),
                         evidence=[f'market_{key}','margin',f'detail_{key}_1',f'detail_{key}_2']))
        prev,prev_etf=m,etf
    probe=result(snapshot,'next_margin_probe','RZRQ_HZ_INFO')
    if probe['result'] or probe['pageHelp']['total']!=0:
        raise ValueError('Unexpected latest-day availability')
    checked=datetime.now(timezone.utc)
    ready=datetime.fromisoformat(ready_at) if ready_at else checked
    if ready.tzinfo is None or not received<=ready<=checked:
        raise ValueError('Impossible audit readiness time')
    return dict(schemaVersion=1,through=rows[-1]['date'],snapshot='data/snapshots/'+SNAPSHOT,
                snapshotSha256=SEAL,receivedAt=received.isoformat(),featureReadyAt=ready.isoformat(),
                publishedAt=None,historicalPointInTime=False,researchOnly=True,rows=rows,
                scope=dict(financing='沪市全体融资融券汇总，含调出标的存量。',
                           turnover='沪市主板A及科创板（含存托凭证）成交额。沪市B股、基金、债券、期权、回购均不计入。',
                           financingBuyShare='分子为当日沪市信用交易明细中600/601/603/605/688/689证券融资买入额，分母为相同日期主板A与科创板成交额。',
                           relativeTurnover20='当日同范围成交额除以前20个完整交易日的算术平均值。'),
                units=dict(money='人民币元',turnoverSource='亿元，各板块原值精度为0.01亿元',ratio='1 表示 100%'),
                balanceCounts=dict(Counter(r['balanceIdentity']['status'] for r in rows)),
                latestProbe=dict(date='2026-11-27',marginRows=0,source='next_margin_probe'),
                sourcePages=dict(margin=MARGIN,turnover=MARKET,codeAllocation=RULE),
                limitations=['历史披露时刻未知。收到与审核时间记录本次补抓，所有字段只能在本次审核后用于资料查询。',
                             '融资净额按买入减偿还列示，余额恒等式残差为公布余额减公式期望值。残差不为零时，仅保留观察值，未核明原因。',
                             '沪市成交额使用交易所各板块已舍入至亿元小数两位的金额，融资买入占比为按这些公布值计算的估算。',
                             '未取得逐日成分、停牌、无前收及新股一致口径的市场广度，下列广度均为空。'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path)
    group.add_argument('--verify',type=Path)
    args=parser.parse_args()
    if args.output:
        create(args.output,build())
    else:
        old=read(args.verify)
        if old!=build(old['featureReadyAt']):
            raise ValueError('Offline report differs')
        print('PASS',len(old['rows']),'days',old['through'],old['balanceCounts'])
