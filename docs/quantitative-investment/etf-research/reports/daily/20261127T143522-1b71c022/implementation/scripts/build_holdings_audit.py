"""Reconcile official H1 tables, explicit denominators and cross-market identities."""
from pathlib import Path
from decimal import Decimal as D, ROUND_HALF_UP
from collections import defaultdict
import argparse,csv,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from etf_research.publication import verify_bundle
SOURCE=ROOT/'data/snapshots/2026-11-06-research-evidence-234940'
IDENTITY=ROOT/'data/snapshots/2026-11-07-bond-identities-000043'


def extract_stocks(text):
    section=text.split('7.3.1 期末指数投资',1)[1].split('7.4 报告期内股票',1)[0]
    chunks=section.split('7.3.2 期末积极投资',1)
    if len(chunks)!=2:raise ValueError('Missing stock tables')
    rows=[]
    pattern=r'^\s*(\d+)\s+(\d{6})\s+([^\r\n]+?)\s+([\d,]+)\s+([\d,]+\.\d{2})\s+(\d+\.\d{2})\s*$'
    for sleeve,chunk,count,total in zip(('index','active'),chunks,(300,39),(D('90985557480.68'),D('17653711.61'))):
        parsed=[]
        for m in re.finditer(pattern,chunk,re.M):
            rank,code,name,quantity,value,percent=m.groups()
            parsed.append(dict(sleeve=sleeve,rank=int(rank),code=code,name=' '.join(name.split()),quantity=int(quantity.replace(',','')),fair_value=value.replace(',',''),reported_percent=percent))
        if [r['rank'] for r in parsed]!=list(range(1,count+1)):raise ValueError('Missing/duplicate stock ranks: '+sleeve)
        if sum((D(r['fair_value']) for r in parsed),D(0))!=total:raise ValueError('Stock sleeve total mismatch')
        rows.extend(parsed)
    return rows


def build(output):
    output.mkdir(parents=True,exist_ok=True)
    for folder in (SOURCE,IDENTITY):verify_bundle(folder)
    text=(SOURCE/'interim_510300.txt').read_text(encoding='utf-8')
    stocks=extract_stocks(text)
    nav=D('94872183996.40');assets=D('95683574830.88');liabilities=D('811390834.48');stock_total=D('91003211192.29')
    if assets-liabilities!=nav:raise ValueError('Stock fund balance sheet mismatch')
    aggregated=defaultdict(lambda:D(0))
    for row in stocks:
        value=D(row['fair_value']);aggregated[row['code']]+=value
        if (100*value/nav).quantize(D('.01'),rounding=ROUND_HALF_UP)!=D(row['reported_percent']):raise ValueError('Stock NAV percent mismatch')
    if sum(aggregated.values(),D(0))!=stock_total:raise ValueError('Full stock total mismatch')
    hhi=sum(((v/stock_total)**2 for v in aggregated.values()),D(0))
    independent=float(np.square(np.array([float(v) for v in aggregated.values()])/float(stock_total)).sum())
    if abs(float(hhi)-independent)>1e-14:raise ValueError('HHI crosscheck mismatch')
    bond_nav=D('5117244931.52');bond_assets=D('5179839036.35');bond_liabilities=D('62594104.83');bond_total=D('5060489774.03')
    if bond_assets-bond_liabilities!=bond_nav:raise ValueError('Bond balance sheet mismatch')
    # Visual transcription of PDF page 35; wrapped last digits checked against rendered PDF.
    bonds=[dict(code=c,quantity=q,fair_value=v,reported_percent=p) for c,q,v,p in [
        ('250020',10400000,'1061756515.07','20.75'),('019793',10361050,'1057780032.71','20.67'),
        ('019834',9082590,'914402812.28','17.87'),('260008',8300000,'835614438.36','16.33'),('019829',5905070,'597607320.89','11.68')]]
    aliases={};identity_rows=[]
    for code in ('019793','019834','019829','019848'):
        result=json.loads((IDENTITY/('identity_'+code+'.body')).read_text())['result']
        if len(result)!=1 or result[0]['BOND_CODE']!=code or result[0]['ISSUE_OWNER']!='财政部':raise ValueError('Unexpected issuer identity')
        row={k:result[0][k] for k in ('BOND_CODE','BANK_CODE','BOND_FULL','ISSUE_OWNER','START_DATE','END_DATE')}
        for alias in (row['BOND_CODE'],row['BANK_CODE']):
            if alias in aliases and aliases[alias]!=row['BOND_FULL']:raise ValueError('Conflicting alias')
            aliases[alias]=row['BOND_FULL']
        identity_rows.append(row)
    grouped=defaultdict(lambda:D(0))
    for row in bonds:
        value=D(row['fair_value'])
        if (100*value/bond_nav).quantize(D('.01'),rounding=ROUND_HALF_UP)!=D(row['reported_percent']):raise ValueError('Bond NAV percent mismatch')
        grouped[aliases[row['code']]]+=value
    covered=sum(grouped.values(),D(0))
    if covered>bond_total:raise ValueError('Disclosed coverage exceeds bond total')
    bond_text=re.sub(r'[\s,]','',(SOURCE/'interim_511010.txt').read_text(encoding='utf-8'))
    stock_text=re.sub(r'[\s,]','',text)
    for value in (nav,assets,liabilities,stock_total):
        if str(value) not in stock_text:raise ValueError('Stock balance absent from extracted original')
    for value in [bond_nav,bond_assets,bond_liabilities,bond_total]+[r['fair_value'] for r in bonds[2:]]:
        if str(value) not in bond_text:raise ValueError('Bond value absent from extracted original')
    page35=(SOURCE/'interim_511010.txt').read_text(encoding='utf-8').split('\f')[34]
    for pattern in (r'1,061,756,515\.0\s+20\.75\s*\n[^\n]*\s7\s*\n',r'1,057,780,032\.7\s+20\.67\s*\n\s*1\s*\n'):
        if not re.search(pattern,page35):raise ValueError('Wrapped value differs from visually reviewed page 35')
    q3=json.loads((ROOT/'data/reference/holdings_2026q3.json').read_text(encoding='utf-8'))['funds']['511010']
    q3group=defaultdict(lambda:D(0))
    for row in q3['listed_positions']:q3group[aliases[row['code']]]+=D(row['fair_value'])
    with (output/'stocks_2026h1.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=stocks[0].keys());w.writeheader();w.writerows(stocks)
    source_paths=[SOURCE/'manifest.json',SOURCE/'interim_510300.pdf',SOURCE/'interim_511010.pdf',IDENTITY/'manifest.json',ROOT/'data/reference/holdings_2026q3.json',Path(__file__)]
    ordered=sorted(aggregated.values(),reverse=True)
    report=dict(schema_version=1,report_date='2026-06-30',financial_statements_audited=False,not_current_holdings=True,not_historical_holdings_series=True,
        announcement_dates={'510300':'2026-08-29','511010':'2026-08-31'},
        sources_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        stock=dict(pdf_pages=[13,46,47,48,49,50,51,52,53,54,55,56],assets=assets,liabilities=liabilities,nav=nav,
            stock_total=stock_total,rows=len(stocks),unique_security_codes=len(aggregated),index_rows=300,active_rows=39,
            stock_fraction_of_nav=stock_total/nav,stock_fraction_of_assets=stock_total/assets,
            top1_fraction_of_nav=ordered[0]/nav,top10_fraction_of_nav=sum(ordered[:10])/nav,
            stock_sleeve_hhi=hhi,stock_sleeve_effective_count=1/hhi,full_fund_hhi=None,ultimate_issuer_hhi=None,
            numpy_decimal_hhi_crosscheck=True,notes='Full disclosed stock sleeve only; excludes refundable substitution valuation adjustments. No real-time or ultimate-owner claim.'),
        bond=dict(pdf_pages=[14,34,35],assets=bond_assets,liabilities=bond_liabilities,nav=bond_nav,bond_total=bond_total,
            government_bond_fraction_of_nav=bond_total/bond_nav,listed_positions=bonds,listed_total=covered,
            listed_fraction_of_nav=covered/bond_nav,listed_fraction_of_bonds=covered/bond_total,
            undisclosed_bond_value=bond_total-covered,full_security_hhi=None,
            known_issue_nav_lower_bounds={k:v/bond_nav for k,v in grouped.items()},issuer_category='中华人民共和国财政部（国家债券）',
            notes='Five codes map to three known issues; unlisted codes remain unknown. Issuer category share is not a full-fund issuer HHI.'),
        identities=identity_rows,q3_separate_observation=dict(report_date='2026-09-30',known_issue_nav_lower_bounds={k:v/D(q3['nav']) for k,v in q3group.items()},full_security_hhi=None),
        visual_review=dict(renderer='PyMuPDF 1.26.7',pages=[13,48,55,56,14,34,35],review='Compared balance sheets, table boundaries, top rows and wrapped bond values; every intermediate stock row is additionally constrained by ranks, exact sums and rounded NAV percentages.'))
    (output/'holdings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(dict(stock_rows=len(stocks),stock_codes=len(aggregated),bond_issues=len(grouped),bond_coverage=float(covered/bond_total))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'reports/2026-11-06-research-audit');a=p.parse_args();build(a.output)
