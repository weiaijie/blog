"""Review the pre-split cross-border ETF history against sealed public captures."""
from datetime import date
import hashlib
import json
import re
from urllib.parse import parse_qs, urlsplit

from pypdf import PdfReader
from audit_suspensions import validate
from etf_research.admission import parse_prices
from etf_research.data import RawBar, verify_manifest
from etf_research.official_history import parse_dayk

FIRST = date(2019, 1, 2)
CAT = '20261110-early-history-catalog-b71d08'
DOC = '20261110-early-history-reports-51a3d2'
ETF = '20261110-early-history-etf-0405c1'
SEALS = {CAT: '0bb1b44ef6f534181dd26f8ef669193d3e8b8829b1dee8aa318728693b4f21fb',
         DOC: '79917dea60c12c99a61b2216e12cb3adccb753d63c7525bc9de1981243569fae',
         ETF: 'a3c3d95d5201b18014aba24e258d43b335a6962555b6d3250e21b10fa04d6d39'}
EVENT = re.compile('停牌|复牌|停复|拆分|分拆|折算|分红|收益分配|份额合并|暂停交易|恢复交易')


def verify_early(snapshots, domestic_days, bars):
    records = {}
    for folder, seal in SEALS.items():
        root = snapshots/folder
        if hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest() != seal:
            raise ValueError('Historical evidence changed: '+folder)
        hashes = verify_manifest(root)
        for row in json.loads((root/'requests.json').read_bytes()):
            name = row['name']
            if row['status']==200 and row['exit_code']==0 and row['url']==row['effective_url'] and row['sha256']==hashes[name+'.body']:
                records[folder,name] = row, root/(name+'.body')

    def document(folder, name):
        return records[folder,name][1]

    archive = snapshots/'2026-11-06-suspension-15'
    verify_manifest(archive)
    register = {r['name']:r for file in ('requests.json','followup_requests.json')
                for r in json.loads((archive/file).read_bytes())}
    for year in (2019, 2020, 2021):
        key = 'sse_'+str(year)
        query = parse_qs(urlsplit(records[CAT,key][0]['url']).query)
        catalog = json.loads(document(CAT,key).read_bytes())
        sh = catalog['result']
        if (query['START_DATE'] != [f'{year}-01-01'] or query['END_DATE'] != [f'{year}-12-31']
            or len({r['URL'] for r in sh}) != len(sh) or len(sh) != catalog['pageHelp']['total']
            or any(r['SECURITY_CODE'] != '513500' or EVENT.search(r['TITLE']) for r in sh)):
            raise ValueError('SSE historical event review required')
        pages = [(CAT,'cn_'+str(year))]
        if year in (2019,2021):
            pages.append((DOC,'cn_'+str(year)+'_2'))
        sz = []
        for i,(folder,name) in enumerate(pages,1):
            meta, file = records[folder,name]
            query = parse_qs(meta['post'])
            page = json.loads(file.read_bytes())
            if (query['stock']!=['159920,jjjl0000031'] or query['seDate']!=[f'{year}-01-01~{year}-12-31']
                or query['pageNum']!=[str(i)] or page['hasMore'] != (i<len(pages))):
                raise ValueError('CNINFO historical pagination mismatch')
            sz.extend(page['announcements'])
        if (len({r['announcementId'] for r in sz})!=len(sz) or len(sz)!=page['totalAnnouncement']
            or any(r['secCode']!='159920' or r['orgId']!='jjjl0000031' or EVENT.search(r['announcementTitle']) for r in sz)):
            raise ValueError('CNINFO historical event review required')
        name = 'all_'+str(year)
        rows, total = validate(register[name], (archive/(name+'.body')).read_bytes())
        if not total or any(r['secCode']=='513500' for r in rows):
            raise ValueError('Review historical SSE suspension register')

    # PDF pages are one-based. The SSE 2020 link returned feeder fund 050025.
    for code, year, profit, split in [('159920',2019,12,48),('159920',2020,13,50),('159920',2021,14,53),
                                     ('513500',2019,16,65),('513500',2020,16,63),('513500',2021,9,61)]:
        folder = ETF if (code,year)==('513500',2020) else DOC
        reader = PdfReader(document(folder,f'annual_{code}_{year}'))
        def page_text(page):
            return ''.join(reader.pages[page-1].extract_text().split())
        first_pages = ''.join(page_text(n) for n in range(1,7))
        match = re.search(r'基金主代码([0-9]{6})',first_pages)
        proof = '本报告期未进行利润分配' if code=='159920' else '本报告期内本基金未进行收益分配'
        if (code,year)==('513500',2021):
            proof = '过去三年基金的利润分配情况无'
        if (not match or match[1]!=code or str(year)+'年年度报告' not in first_pages
            or proof not in page_text(profit) or '本报告期基金拆分变动份额-本报告期期末' not in page_text(split)):
            raise ValueError('Unmatched historical ETF annual report')

    sessions = [d for d in domestic_days if FIRST <= d <= date(2021,12,31)]
    for code in ('513500','159920'):
        official = parse_dayk(document(CAT,'quotes_'+code).read_text(),code)
        if [d for d in official if FIRST<=d<=sessions[-1]]!=sessions or any(
                RawBar(d,**official[d])!=bars[code][d] for d in sessions):
            raise ValueError('Historical exchange price/calendar mismatch: '+code)
        folder = CAT if code=='513500' else DOC
        sohu = parse_prices(document(folder,'sohu_2021_'+code).read_bytes(),'sohu',sessions[-1])
        if list(sorted(sohu))!=[d for d in sessions if d.year==2021] or any(
                bar!=bars[code][d] for d,bar in sohu.items()):
            raise ValueError('Historical third-source mismatch: '+code)
