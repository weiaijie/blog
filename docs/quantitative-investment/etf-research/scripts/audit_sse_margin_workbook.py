"""Compare the optional SSE XLS download with the archived official JSON responses."""
import argparse
from datetime import date
import json
from pathlib import Path
import re

from market_state_pilot import amount
from etf_research.evidence_archive import object_path, verify as verify_archive
from etf_research.publication import read, sha, verify_bundle

SUMMARY = dict(rzye='本日融资余额(元)',rzmre='本日融资买入额(元)',rqyl='本日融券余量',
               rqylje='本日融券余量金额(元)',rqmcl='本日融券卖出量',rzrqjyzl='本日融资融券余额(元)')
DETAIL = dict(rzye='本日融资余额(元)',rzmre='本日融资买入额(元)',rzche='本日融资偿还额(元)',
              rqyl='本日融券余量',rqmcl='本日融券卖出量',rqchl='本日融券偿还量')


def integer(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9]+',value):
        raise ValueError('Expected integer text in the SSE workbook')
    return int(value)


def read_table(sheet, fields, identifiers=()):
    header=(*identifiers,*fields.values())
    if tuple(sheet.row_values(0))!=header:
        raise ValueError('SSE workbook columns changed: '+sheet.name)
    rows=[]
    for number in range(1,sheet.nrows):
        row=sheet.row_values(number)
        if not any(row):
            continue
        if not identifiers and isinstance(row[0],str) and row[0].startswith('注：') and not any(row[1:]):
            continue
        rows.append(dict(zip(identifiers,row[:len(identifiers)],strict=True),
                         **{field:integer(value) for field,value in zip(fields,row[len(identifiers):],strict=True)}))
    return rows


def audit(snapshot, store, identity, day, workbook_reader):
    verify_bundle(snapshot)
    tag=day.strftime('%Y%m%d')
    name='margin_overview_'+tag
    request,=[row for row in read(snapshot/'requests.json') if row['name']==name]
    workbook=snapshot/(name+'.body')
    url='https://www.sse.com.cn/market/dealingdata/overview/margin/a/rzrqjygk'+tag+'.xls'
    if (request['url']!=url or request['final_url']!=url or request['status']!=200 or request['curl_exit']
            or request['metrics']['ssl_verify_result']!=0 or request['sha256']!=sha(workbook)):
        raise ValueError('Official dated workbook unavailable or changed')
    book=workbook_reader(file_contents=workbook.read_bytes())
    official_summary,=read_table(book.sheet_by_name('汇总信息'),SUMMARY)
    code='标的证券代码'
    official=read_table(book.sheet_by_name('明细信息'),DETAIL,(code,'标的证券简称'))
    if len(official)!=len({row[code] for row in official}):
        raise ValueError('Official workbook has duplicate security codes')
    archived=verify_archive(store,identity)
    selected=[(Path(key).name,value) for key,value in archived['files'].items()
              if key.startswith('reports/research-observation/runs/') and '-sse-research-day/' in key and
              (key.endswith('/margin.body') or re.search(fr'/detail_{tag}_[0-9]+\.body$',key))]
    files=dict(selected)
    if len(files)!=len(selected) or 'margin.body' not in files:
        raise ValueError('Choose one exact-date official JSON archive')
    def payload(which):
        return json.loads(object_path(store,files[which]['sha256']).read_bytes())['result']
    summary,=[row for row in payload('margin.body') if row['opDate']==tag]
    rows=[row for page in sorted(files) if page!='margin.body' for row in payload(page)]
    detail={row['stockCode']:row for row in rows}
    if (not rows or len(detail)!=len(rows) or any(row['opDate']!=tag for row in rows)
            or set(detail)!={row[code] for row in official}
            or any(official_summary[field]!=amount(summary,field) for field in SUMMARY)
            or any(row[field]!=amount(detail[row[code]],field) for field in DETAIL for row in official)):
        raise ValueError('Same-day XLS and JSON records differ')
    repayment=sum(row['rzche'] for row in official)
    summary_repayment=amount(summary,'rzche')
    return dict(date=day.isoformat(),jsonArchiveSha256=identity,workbookSha256=request['sha256'],
                workbookReceivedAt=request['receivedAt'],securityRows=len(official),
                matchingSummaryFields=len(SUMMARY),matchingDetailFields=len(DETAIL)*len(official),
                detailRepaymentCny=repayment,marketRepaymentCny=summary_repayment,
                detailMinusMarketRepaymentCny=repayment-summary_repayment)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--archive-store',type=Path,required=True)
    parser.add_argument('--archive',required=True)
    parser.add_argument('--day',type=date.fromisoformat,required=True)
    args=parser.parse_args()
    try:
        from xlrd import open_workbook
    except ImportError:
        parser.error('Install xlrd==2.0.2 in the optional audit environment to read legacy XLS files')
    output=audit(args.snapshot,args.archive_store,args.archive,args.day,open_workbook)
    print(json.dumps(output,ensure_ascii=False))


if __name__=='__main__':
    main()
