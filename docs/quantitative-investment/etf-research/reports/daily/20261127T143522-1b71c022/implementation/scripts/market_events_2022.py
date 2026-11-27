"""Reviewed 2022 disclosures for the two exchange-listed cross-border ETFs."""
from datetime import date
import hashlib
import json
import re
from urllib.parse import parse_qs, urlparse

from pypdf import PdfReader
from etf_research.data import verify_manifest
from audit_suspensions import validate

FIRST_2022 = date(2022, 1, 4)
SPLIT_DAY = date(2022, 3, 29)
RESUMED = date(2022, 3, 30)
FOLDER = '20261110T104658-markets-2022-f2vzkjbg'
SEAL = 'b67281ed6aa6aa6bcf5cac4caf62eb6fa2b0642db90f6fca6a03385b5312283a'


def verify_2022(snapshots):
    folder = snapshots/FOLDER
    if hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest() != SEAL:
        raise ValueError('2022 disclosure snapshot changed; review required')
    verify_manifest(folder)
    records = {r['name']:r for r in map(json.loads,(folder/'requests.jsonl').read_text().splitlines())}

    def source(name):
        record = records[name]
        path = folder/(name+'.body')
        if (record['status'] != 200 or record['exit_code'] or record['error']
                or record['sha256'] != hashlib.sha256(path.read_bytes()).hexdigest()):
            raise ValueError('Unverified 2022 disclosure: '+name)
        return path

    sse = json.loads(source('sse_2022').read_bytes())
    cn = json.loads(source('cn_1').read_bytes())
    query = parse_qs(urlparse(records['sse_2022']['url']).query)
    post = parse_qs(records['cn_1']['post'])
    sh, sz = sse['result'], cn['announcements']
    if (query['START_DATE'] != ['2022-01-01'] or query['END_DATE'] != ['2022-12-31']
            or post['seDate'] != ['2022-01-01~2022-12-31'] or cn['hasMore']
            or len({r['URL'] for r in sh}) != len(sh) or len(sh) != sse['pageHelp']['total']
            or len({r['announcementId'] for r in sz}) != len(sz) or len(sz) != cn['totalAnnouncement']
            or any(r['SECURITY_CODE'] != '513500' for r in sh)
            or any(r['secCode'] != '159920' or r['orgId'] != 'jjjl0000031' for r in sz)):
        raise ValueError('Incomplete or mismatched 2022 fund catalog')
    relevant = re.compile('停牌|复牌|停复|拆分|分拆|折算|分红|收益分配|份额合并|暂停交易|恢复交易')
    dates = []
    for row in sh:
        if relevant.search(row['TITLE']):
            key = 'split_'+row['SSEDATE']
            source(key)
            if records[key]['url'] != 'https://www.sse.com.cn'+row['URL']:
                raise ValueError('2022 event document differs from catalog')
            dates.append(row['SSEDATE'])
    if sorted(dates) != ['2022-03-18','2022-03-23','2022-03-28','2022-03-30'] or any(
            relevant.search(r['announcementTitle']) for r in sz):
        raise ValueError('Unreviewed 2022 fund event')

    # Reviewed pages, one-based as in the PDF reader.
    for key, page, fragments in (
            ('annual_513500',14,['本报告期内本基金未进行收益分配']),
            ('annual_513500',74,['本报告期基金拆分变动份额2,560,819,285.00']),
            ('annual_159920',14,['本基金本报告期未进行利润分配']),
            ('annual_159920',59,['本报告期基金拆分变动份额-本报告期期末']),
            ('split_2022-03-30',1,['本基金基金份额拆分比例为1:2','2022年3月28日','2022年3月30日起恢复交易'])):
        text = ''.join(PdfReader(source(key)).pages[page-1].extract_text().split())
        if not all(fragment in text for fragment in fragments):
            raise ValueError('2022 corporate action review mismatch: '+key)
    # Independently bind the trading halt to the exchange register.
    archive = snapshots/'2026-11-06-suspension-15'
    verify_manifest(archive)
    meta = next(r for r in json.loads((archive/'followup_requests.json').read_bytes())+
                json.loads((archive/'requests.json').read_bytes()) if r['name']=='all_2022')
    rows, _ = validate(meta,(archive/'all_2022.body').read_bytes())
    events = [(r['startStopDate'],r['endStopDate'],r['startStopReason'])
              for r in rows if r['secCode']=='513500']
    if events != [('20220329','20220329','份额拆分')]:
        raise ValueError('2022 SSE suspension register mismatch')
