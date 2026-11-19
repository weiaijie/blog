"""Same-quarter NAV-level look-through and separately dated A/H evidence."""
import csv
import re
from decimal import Decimal as D, ROUND_HALF_UP

from pypdf import PdfReader

from extract_holdings import extract
from market_evidence import ROOT, source

US = [('NVDA','英伟达'), ('AAPL','苹果'), ('MSFT','微软'), ('GOOGL','Alphabet'),
      ('GOOG','Alphabet'), ('AMZN','亚马逊'), ('AVGO','博通'), ('META','Meta'),
      ('MU','美光'), ('TSLA','特斯拉'), ('AMD','AMD')]
HK = [('00005','汇丰控股'), ('00700','腾讯控股'), ('09988','阿里巴巴'), ('00939','建设银行'),
      ('01299','友邦保险'), ('01398','工商银行'), ('00941','中国移动'), ('00388','香港交易所'),
      ('01810','小米集团'), ('03988','中国银行')]
NUMBER = r'(\d{1,3}(?:,\d{3})*\.\d{2})'
# Security-class pairs reviewed against the names printed in both June reports.
AH = [('00939','601939','建设银行'), ('01398','601398','工商银行'), ('00941','600941','中国移动'),
      ('03988','601988','中国银行'), ('02318','601318','中国平安'), ('03968','600036','招商银行'),
      ('03750','300750','宁德时代'), ('02899','601899','紫金矿业'), ('02359','603259','药明康德'),
      ('00300','000333','美的集团'), ('01211','002594','比亚迪'), ('02628','601628','中国人寿'),
      ('01088','601088','中国神华'), ('00386','600028','中国石化'), ('03993','603993','洛阳钼业'),
      ('00728','601728','中国电信'), ('06690','600690','海尔智家'), ('02600','601600','中国铝业'),
      ('00981','688981','中芯国际'), ('00883','600938','中国海油')]


def num(s):
    return D(s.replace(',', ''))


def pct(value, nav):
    return (D(100)*value/nav).quantize(D('.01'), rounding=ROUND_HALF_UP)


def published_row(table, token, geography):
    match = re.search(token + geography + NUMBER + NUMBER + r'(\d{1,2}\.\d{2})', table)
    if not match:
        raise ValueError('Cannot read disclosed security ' + token)
    return [num(s) for s in match.groups()]


def foreign_fund(items, code):
    path = source(items, 'q3_' + code)
    pages = [p.extract_text() for p in PdfReader(path).pages]
    if '2026年9月30日' not in ''.join(pages[0].split()):
        raise ValueError('Unexpected portfolio date')
    text = '\n'.join(pages)
    nav = num(re.search(r'期末基金资产净值\s*([\d,]+\.\d+)', text)[1])
    sector_text = text.split('行业类别')[-1].split('合计',1)
    sectors = {}
    for name, value, percent in re.findall(r'^\s*([^\s\d]+)\s+([\d,]+\.\d{2})\s+(\d+\.\d{2})\s*$', sector_text[0], re.M):
        if pct(num(value), nav) != D(percent) or name in sectors:
            raise ValueError('Sector weight mismatch')
        sectors[name] = dict(fair_value=num(value), percent=D(percent))
    total = re.match(r'\s*([\d,]+\.\d{2})\s+(\d+\.\d{2})',sector_text[1])
    if len(sectors) != 11 or sum(r['fair_value'] for r in sectors.values()) != num(total[1]):
        raise ValueError('Incomplete industries')
    compact = ''.join(text.split()).split('行业类别')[-1].split('注：所用证券代码')[0]
    positions, companies = [], {}
    us = code == '513500'
    for symbol, issuer in US if us else HK:
        qty, fair, reported = published_row(compact, symbol + ('US' if us else ''),
                                            '纳斯(?:达克交易所)?美国' if us else '香港联合交易所中国香港')
        if pct(fair,nav) != reported:
            raise ValueError('Disclosed NAV weight mismatch: ' + symbol)
        positions.append(dict(code=symbol, name=issuer, quantity=qty, fair_value=fair, percent=reported))
        companies[issuer] = companies.get(issuer, D(0)) + fair
    return dict(nav=nav, source=items['q3_'+code][1]['url'], positions=positions, sectors=sectors,
                companies={k:pct(v,nav) for k,v in companies.items()},
                top10_percent=pct(sum(companies.values()),nav), equity_percent=num(total[2]))


def holdings_report(items):
    base = extract()['funds']
    a = base['510300']
    nav = D(a['nav'])
    funds = {'510300': dict(nav=nav, source=a['official_url'], positions=a['listed_positions'],
                           sectors={r['name']:dict(percent=pct(D(r['fair_value']),nav),fair_value=r['fair_value'])
                                    for r in a['sectors'].values()},
                           companies={r['name']:D(r['reported_percent']) for r in a['listed_positions']},
                           top10_percent=pct(D(a['listed_nav_fraction'])*nav,nav),
                           equity_percent=pct(D(a['security_nav_fraction'])*nav,nav))}
    funds.update({s:foreign_fund(items,s) for s in ('513500','159920')})
    overlaps = {a+' / '+b:sorted(set(funds[a]['companies']) & set(funds[b]['companies']))
                for a,b in [('510300','513500'),('510300','159920'),('513500','159920')]}
    june = PdfReader(source(items,'h1_159920'))
    table = ''.join(''.join(''.join(p.extract_text().splitlines()[2:]).split()) for p in june.pages[38:47])
    # June has its own date, holdings, and denominator.
    if '2026年6月30日' not in ''.join(june.pages[0].extract_text().split()):
        raise ValueError('Unexpected interim portfolio date')
    with (ROOT/'reports/2026-11-06-research-audit/stocks_2026h1.csv').open(encoding='utf-8') as f:
        a_positions = {r['code']:r for r in csv.DictReader(f) if r['sleeve']=='index'}
    pairs = []
    for h, a_code, name in AH:
        qty, value, weight = published_row(table,h,'香港联合交易所中国香港')
        r = a_positions[a_code]
        if r['name'] != name or not qty or not value:
            raise ValueError('Incorrect A/H issuer mapping ' + name)
        pairs.append(dict(company=name, a_code=a_code, hk_code=h, a_nav_pct=r['reported_percent'],
                          hk_nav_pct=weight, equal_portfolio_pct_from_printed_weights=(D(r['reported_percent'])+weight)/6))
    return dict(quarter='2026-09-30', announced='2026-10-27', funds=funds,
                overlap_among_disclosed_top10=overlaps, bond=base['511010'],
                earlier_ah_date='2026-06-30', earlier_verified_pairs_lower_bound=pairs)
