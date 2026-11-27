"""Collect official policy candidates and cleared-unit/NAV values for one research day."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from decimal import DecimalException
import hashlib
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4
from xml.etree.ElementTree import ParseError

from collect_sse_research_day import CALENDAR, CALENDAR_SHA, ROOT, previous_session
from etf_share_flow import SEAL, SHARES_QUERY, SYMBOLS, conversion_basis, estimate, guotai_nav, huatai_nav
from etf_share_flow import number, read_sources, shares_for
from policy_source_watch import INDEXES, candidate, index_candidates
from etf_research.admission import sessions_between
from etf_research.http_capture import fetch, load_policy, save_transport
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, read, seal, sha, verify_bundle

HOSTS = ('www.gov.cn', 'www.csrc.gov.cn', 'www.huatai-pb.com', 'm.gtfund.com')
SSE = 'https://query.sse.com.cn/commonQuery.do?'
HUATAI = 'https://www.huatai-pb.com/common-web/chart/fundnettable/getFundNetTableJson?'
GUOTAI = 'https://m.gtfund.com/cochin/etf/download/511010/'
POLICY_CAP = 16
MALFORMED = (ValueError, TypeError, KeyError, IndexError, DecimalException, ParseError)


def following_session(day):
    holidays = read(CALENDAR)['holiday_ranges']
    for delta in range(1, 32):
        possible = day + timedelta(days=delta)
        if str(possible.year) not in holidays:
            return None
        if sessions_between(holidays, possible, possible):
            return possible
    return None


def page_params(size):
    return {'isPagination':'true','pageHelp.pageSize':size,'pageHelp.pageNo':1,
            'pageHelp.beginPage':1,'pageHelp.endPage':1,'pageHelp.cacheSize':1}


def planned(day, prior, following):
    jobs = dict(INDEXES)
    for d in (prior, day):
        jobs['shares_'+d.strftime('%Y%m%d')] = SSE + urlencode({
            'sqlId':SHARES_QUERY,'STAT_DATE':str(d),**page_params(1500)})
    jobs['nav_510300'] = HUATAI + urlencode({
        'fundcode':'510300','from':str(prior),'to':str(day),'pages':'1-10',
        'siteId':'9496d23c648f4a72a79150c3f2ac669b'})
    for d in (day, following):
        if d:
            stamp = d.strftime('%Y%m%d')
            jobs['nav_511010_'+stamp] = GUOTAI+stamp
    for code in SYMBOLS:
        jobs['catalog_'+code] = SSE + urlencode({
            'sqlId':'COMMON_PL_JJXX_JJGG_NEW_L','SECURITY_CODE':code,'TITLE':'',
            'START_DATE':'2012-01-01','END_DATE':str(day),**page_params(1000)})
    return jobs


def discovery(folder, records):
    articles, issues = {}, {}
    for name in INDEXES:
        record = records[name]
        if not usable(record):
            issues[name] = 'Official index unavailable'
            continue
        try:
            observed = instant(record['receivedAt']).astimezone(TZ).date()
            articles.update(index_candidates(name, (folder/(name+'.body')).read_bytes(), observed))
        except MALFORMED as error:
            issues[name] = str(error)
    if len(articles) > POLICY_CAP:
        issues['article_limit'] = f'{len(articles)} candidates exceed the limit of {POLICY_CAP}'
    selected = list(articles.values())[:POLICY_CAP]
    return {'policy_'+hashlib.sha256(row['url'].encode()).hexdigest()[:20]:row for row in selected}, issues


def usable(record):
    return (record['status']==200 and not record['curl_exit'] and not record.get('error')
            and record['url']==record['final_url'] and record['metrics']['ssl_verify_result']==0)


def fund_rows(folder, available, day, prior, following, ready):
    audited_basis = read_sources()
    for code in SYMBOLS:
        issues = {}
        columns, huatai = {}, {}
        for d in (prior,day):
            key = 'shares_'+d.strftime('%Y%m%d')
            try:
                _, units, _ = shares_for(d,available,folder)
                columns[d] = units[code]
            except MALFORMED:
                issues[key] = 'Cleared units absent or incomplete'
        if code == '510300':
            try:
                huatai = huatai_nav((prior,day), available, folder)
            except MALFORMED:
                issues['nav_510300'] = 'Manager NAV series is unavailable or invalid'
        navs = {}
        for valuation, effective in ((prior,day),(day,following)):
            try:
                if code == '510300':
                    navs[valuation] = huatai[valuation][0]
                elif effective is not None:
                    navs[valuation] = guotai_nav(valuation,effective,available,folder)[0]
                else:
                    raise ValueError('Next exchange session unknown')
            except MALFORMED:
                issues['nav_'+str(valuation)] = 'Same-valuation-date manager NAV is absent or unverified'
        catalog = 'catalog_'+code
        try:
            sources = {**audited_basis, catalog:available[catalog]}
            comparable = conversion_basis(code, prior, day, sources, snapshot=folder)
            if not comparable:
                raise ValueError('Conversion history changed')
        except MALFORMED:
            comparable = False
            issues[catalog] = 'Conversion or currency basis needs review'
        flow, intensity = estimate((columns.get(prior),navs.get(prior)),
                                   (columns.get(day),navs.get(day)), comparable=comparable, adjacent=True)
        yield dict(symbol=code, date=str(day), previousDate=str(prior),
                   previousShares=number(columns.get(prior)), totalShares=number(columns.get(day)),
                   previousUnitNav=number(navs.get(prior)), unitNav=number(navs.get(day)),
                   estimatedNetSubscriptionCny=number(flow), relativeIntensity=number(intensity),
                   status='verified_estimate' if flow is not None else 'unknown',
                   featureReadyAt=ready.isoformat() if flow is not None else None, issues=issues)


def inspect(folder, ready):
    run = read(folder/'run.json')
    started = instant(run['startedAt'])
    day = date.fromisoformat(run['date'])
    prior = previous_session(day, started)
    following = following_session(day)
    if (run['previousDate']!=str(prior) or run['followingDate']!=(str(following) if following else None)
            or run['calendarSha256']!=CALENDAR_SHA or run['fundBasisSha256']!=SEAL
            or not started <= ready <= datetime.now(timezone.utc)):
        raise ValueError('Invalid capture calendar or timestamps')
    expected = planned(day, prior, following)
    rows = read(folder/'requests.json')
    records = {r['name']:r for r in rows}
    articles, policy_issues = discovery(folder, records)
    expected.update({key:row['url'] for key,row in articles.items()})
    if len(records)!=len(rows) or list(records)!=list(expected):
        raise ValueError('Unexpected request inventory')
    available, failures = {}, {}
    for name, url in expected.items():
        r = records[name]
        receipt = instant(r['receivedAt'])
        path = folder/(name+'.body')
        if (r['url']!=url or sha(path)!=r['sha256'] or path.stat().st_size!=r['bytes']
                or not started <= instant(r['requested_at_utc']) <= receipt <= ready):
            raise ValueError('Unbound source: '+name)
        if usable(r):
            available[name] = r
        else:
            failures[name] = dict(httpStatus=r['status'],curlExit=r['curl_exit'],error=r.get('error'))
    candidates = []
    for name, item in articles.items():
        try:
            r = available[name]
            publication = candidate((folder/(name+'.body')).read_bytes(),item,instant(r['receivedAt']),ready)
            candidates.append(dict(**publication, evidence=name+'.body'))
        except MALFORMED as error:
            policy_issues[name] = 'Official article unavailable' if name not in available else str(error)
    etf = list(fund_rows(folder,available,day,prior,following,ready))
    return dict(schemaVersion=1, date=str(day), previousDate=str(prior), researchOnly=True,
                runKind='validation', checkedAt=ready.isoformat(), receivedAt=max(
                    instant(row['receivedAt']) for row in rows).isoformat(),
                fundBasisSha256=run['fundBasisSha256'],
                policy={'status':'coverage_incomplete' if policy_issues else 'archived',
                        'candidates':candidates,'issues':policy_issues},
                etf=etf, transportFailures=failures)


def collect(day, parent):
    started = datetime.now(timezone.utc)
    prior, following = previous_session(day,started), following_session(day)
    folder = parent/(started.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8]+'-policy-etf-day')
    folder.mkdir(parents=True,exist_ok=False)
    policy = load_policy()
    save_transport(folder,policy)
    create(folder/'run.json',dict(date=str(day),previousDate=str(prior),
                                 followingDate=str(following) if following else None,
                                 calendarSha256=CALENDAR_SHA,fundBasisSha256=SEAL,startedAt=started.isoformat()))

    def grab(job):
        name,url = job
        row = fetch(folder,name,url,policy,additional_hosts=HOSTS)
        return dict(**row,receivedAt=datetime.now(timezone.utc).isoformat())

    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(grab,planned(day,prior,following).items()))
        articles,_ = discovery(folder,{r['name']:r for r in rows})
        rows.extend(pool.map(grab,((name,article['url']) for name,article in articles.items())))
    create(folder/'requests.json',rows)
    result = inspect(folder,datetime.now(timezone.utc))
    create(folder/'result.json',result)
    seal(folder)
    return folder, verify(folder)


def verify(folder):
    verify_bundle(folder)
    saved = read(folder/'result.json')
    if saved != inspect(folder,instant(saved['checkedAt'])):
        raise ValueError('Official evidence does not reproduce')
    return saved


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--day',type=date.fromisoformat)
    actions.add_argument('--verify',type=Path)
    parser.add_argument('--output-parent',type=Path,default=ROOT/'data/snapshots')
    args = parser.parse_args()
    path, report = (args.verify,verify(args.verify)) if args.verify else collect(args.day,args.output_parent)
    print(path, report['policy']['status'], [(row['symbol'],row['status']) for row in report['etf']])
