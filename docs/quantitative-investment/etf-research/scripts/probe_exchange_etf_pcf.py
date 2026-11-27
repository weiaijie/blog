"""Compare SSE's public 511010 PCF with the manager copy at the actual receipt time."""
import argparse
import json
from datetime import date, datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4
from xml.etree.ElementTree import ParseError

from collect_policy_etf_day import GUOTAI, HOSTS, ROOT, SSE, following_session, usable
from etf_share_flow import guotai_nav
from market_state_pilot import result
from etf_research.admission import completed_date, sessions_between
from etf_research.exchange_calendar import calendar_at
from etf_research.http_capture import fetch, load_policy, save_transport
from etf_research.policy_events import instant
from etf_research.publication import create, read, seal, sha, verify_bundle

EXCHANGE_SQL = 'COMMON_SSE_CP_JJLB_ETFJJGK_GGSGSHQD_JBXX_C'
EXCHANGE_URL = SSE + urlencode({'isPagination':'false','FUNDID2':'511010','sqlId':EXCHANGE_SQL})
TOLERANCE = D('.0005')
EXACT_SOURCE = '国泰基金管理有限公司'


def exchange_record(folder, valuation, effective):
    rows=result(folder,'exchange',EXCHANGE_SQL)['result']
    if len(rows)!=1:
        raise ValueError('Public PCF query did not return exactly one fund')
    row=rows[0]
    if (row['TRADE_CODE']!='511010' or row['FUND_COMP_NAME']!=EXACT_SOURCE
            or not row['NAV'].startswith('￥') or not row['NAVPERCU'].startswith('￥')):
        raise ValueError('Wrong fund, manager or RMB denomination')
    nav=D(row['NAV'][1:])
    units=D(row['CREATION_REDEMPTION_UNIT'])
    basket=D(row['NAVPERCU'][1:])
    if (any(not value.is_finite() or value<=0 for value in (nav,units,basket))
            or units!=units.to_integral_value() or abs(basket/units-nav)>TOLERANCE):
        raise ValueError('Public NAV does not reconcile with the creation basket')
    valuation_day=date.fromisoformat(row['PRE_TRADING_DAY'])
    effective_day=date.fromisoformat(row['TRADING_DAY'])
    same=(valuation_day,effective_day)==(valuation,effective)
    return dict(state='exact_dates' if same else 'different_dates',valuationOn=valuation_day.isoformat(),
                effectiveOn=effective_day.isoformat(),navCny=str(nav))


def capture_plan(day, started, pinned=None):
    calendar=calendar_at(ROOT,started,pinned=pinned)
    if day>completed_date(started) or sessions_between(calendar.ranges,day,day)!=(day,):
        raise ValueError('Valuation date is not a completed verified trading session')
    effective=following_session(day,calendar)
    if effective is None:
        raise ValueError('Next exchange session is unknown')
    stamp=effective.strftime('%Y%m%d')
    return calendar,effective,{'exchange':EXCHANGE_URL,'nav_511010_'+stamp:GUOTAI+stamp}


def analyze(folder, checked):
    run=read(folder/'run.json')
    started=instant(run['startedAt'])
    day=date.fromisoformat(run['valuationOn'])
    _,effective,jobs=capture_plan(day,started,pinned=run['calendarSha256'])
    if run['effectiveOn']!=effective.isoformat():
        raise ValueError('Unverified PCF date binding')
    rows=read(folder/'requests.json')
    if [row['name'] for row in rows]!=list(jobs):
        raise ValueError('Unexpected PCF source inventory')
    current={}
    for row in rows:
        name=row['name']
        if (row['url']!=jobs[name] or sha(folder/(name+'.body'))!=row['sha256']
                or not started<=instant(row['requested_at_utc'])<=instant(row['receivedAt'])<=checked):
            raise ValueError('Unbound PCF capture')
        current[name]=row
    meta=current['exchange']
    manager_name=next(key for key in jobs if key!='exchange')
    manager=current[manager_name]
    public_value={'state':'unavailable'}
    manager_value={'state':'unavailable'}
    # Transport failures, malformed responses, and a previous effective date are distinct results.
    try:
        if usable(meta):
            public_value=exchange_record(folder,day,effective)
    except (ValueError,KeyError,TypeError,ArithmeticError) as error:
        public_value=dict(state='unverified',reason=str(error))
    try:
        if usable(manager):
            nav,_=guotai_nav(day,effective,current,folder)
            manager_value=dict(state='exact_dates',navCny=str(nav))
    except (ValueError,KeyError,TypeError,ArithmeticError,ParseError) as error:
        manager_value=dict(state='unverified',reason=str(error))
    for value,row in ((public_value,meta),(manager_value,manager)):
        value.update(httpStatus=row['status'],sha256=row['sha256'],receivedAt=row['receivedAt'])
    same=public_value['state']==manager_value['state']=='exact_dates'
    match=D(public_value['navCny'])==D(manager_value['navCny']) if same else None
    return dict(schemaVersion=1,researchOnly=True,valuationOn=day.isoformat(),effectiveOn=effective.isoformat(),
                checkedAt=checked.isoformat(),exchange=public_value,manager=manager_value,matched=match)


def collect(day, output):
    started=datetime.now(timezone.utc)
    calendar,effective,jobs=capture_plan(day,started)
    folder=output/(started.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8]+'-pcf')
    folder.mkdir(parents=True,exist_ok=False)
    policy=load_policy()
    save_transport(folder,policy)
    create(folder/'run.json',dict(valuationOn=day.isoformat(),effectiveOn=effective.isoformat(),
                                  calendarSha256=calendar.digest,startedAt=started.isoformat()))
    rows=[]
    for name,url in jobs.items():
        response=fetch(folder,name,url,policy,additional_hosts=HOSTS)
        response['receivedAt']=datetime.now(timezone.utc).isoformat()
        rows.append(response)
    create(folder/'requests.json',rows)
    report=analyze(folder,datetime.now(timezone.utc))
    create(folder/'result.json',report)
    seal(folder)
    return folder,report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    select=parser.add_mutually_exclusive_group(required=True)
    select.add_argument('--day',type=date.fromisoformat)
    select.add_argument('--verify',type=Path)
    parser.add_argument('--output-parent',type=Path)
    args=parser.parse_args()
    if args.verify:
        folder=args.verify
        verify_bundle(folder)
        saved=read(folder/'result.json')
        report=analyze(folder,instant(saved['checkedAt']))
        if report!=saved:
            raise ValueError('PCF comparison did not reproduce')
    else:
        if args.output_parent is None:
            parser.error('--day requires --output-parent')
        folder,report=collect(args.day,args.output_parent)
    print(json.dumps(dict(folder=str(folder),report=report),ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    main()
