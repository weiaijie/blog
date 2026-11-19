"""Extract narrowly identified Q3 tables; fail if totals or rounded ratios differ."""
from pathlib import Path
from decimal import Decimal as D,ROUND_HALF_UP
import argparse,hashlib,json,re
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def amount(s):return D(s.replace(',',''))
def extract():
    folder=ROOT/'data/snapshots/2026-11-06-holdings-windows-1720'
    manifest=json.loads((folder/'manifest.json').read_text())
    for name,sha in manifest.items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=sha:raise ValueError('Holdings snapshot hash mismatch')
    selected=json.loads((folder/'selection.json').read_text(encoding='utf-8'));funds={}
    for code in ('510300','511010'):
        path=folder/f'quarterly_{code}.pdf';pages=[p.extract_text() for p in PdfReader(path).pages]
        if not re.search(r'2026\s*年\s*9\s*月\s*30\s*日',pages[0]):raise ValueError('Unexpected reporting date')
        nav=amount(re.search(r'期末基金资产净值\s+([\d,]+\.\d+)',pages[2]).group(1))
        page=pages[8] if code=='510300' else pages[9]
        start='5.3.1' if code=='510300' else '5.5'
        end='5.3.2' if code=='510300' else '5.6'
        table=page.split(start,1)[1].split(end,1)[0]
        rows=[]
        for rank,symbol,name,qty,value,pct in re.findall(r'^\s*(\d+)\s+(\d{6})\s+(.+?)\s+([\d,]+)\s+([\d,]+\.\d{2})\s+(\d+\.\d+)\s*$',table,re.M):
            fair=amount(value);weight=fair/nav
            if (weight*100).quantize(D('.01'),rounding=ROUND_HALF_UP)!=D(pct):raise ValueError('Holding ratio differs from NAV denominator')
            rows.append(dict(rank=int(rank),code=symbol,name=name,quantity=int(qty.replace(',','')),fair_value=str(fair),reported_percent=pct,nav_fraction=str(weight)))
        if [r['rank'] for r in rows]!=list(range(1,11 if code=='510300' else 6)):raise ValueError('Incomplete/ambiguous holdings table')
        security_total=D('103881848894.77') if code=='510300' else D('7189758682.51')
        # Check constants against captured financial tables, not against a guessed value.
        compact=''.join(pages).replace(',','')
        if str(security_total) not in compact:raise ValueError('Asset total missing from report')
        sectors={}
        if code=='510300':
            text=pages[7]+'\n'+pages[8].split('5.2.3',1)[0]
            for sector,label,value,pct in re.findall(r'^\s*([A-S])\s+(.+?)\s+([\d,]+\.\d{2})\s+(\d+\.\d+)\s*$',text,re.M):
                fair=amount(value)
                if (fair/nav*100).quantize(D('.01'),rounding=ROUND_HALF_UP)!=D(pct):raise ValueError('Sector ratio mismatch')
                prior=sectors.setdefault(sector,dict(name=label,fair_value=D(0)))
                prior['fair_value']+=fair
            if sum(x['fair_value'] for x in sectors.values())!=security_total:raise ValueError('Industry total does not equal stock assets')
        fund=dict(report_date='2026-09-30',announcement_date='2026-10-27',nav=str(nav),
            pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pdf_path=str(path.relative_to(ROOT)).replace('\\','/'),
            official_url=next(s['url'] for s in selected if s['symbol']==code),pages={'net_assets':3,'holdings':9 if code=='510300' else 10},
            listed_positions=rows,security_nav_fraction=str(security_total/nav),listed_nav_fraction=str(sum(D(x['fair_value']) for x in rows)/nav),
            full_security_hhi=None,coverage='index top ten stocks' if code=='510300' else 'top five bond code rows; cross-market aliases not consolidated')
        fund['unlisted_security_nav_fraction']=str(security_total/nav-sum(D(x['nav_fraction']) for x in rows))
        fund['known_hhi_contribution']=str(sum(D(x['nav_fraction'])**2 for x in rows))
        fund['sectors']={k:{'name':v['name'],'fair_value':str(v['fair_value']),'nav_fraction':str(v['fair_value']/nav)} for k,v in sectors.items()}
        if code=='511010':fund['issuer_category']={'name':'中国中央政府（国家债券）','nav_fraction':str(security_total/nav),'source_page':10}
        funds[code]=fund
    return dict(schema_version=1,not_current_holdings=True,not_historical_holdings_series=True,funds=funds)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=extract();a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Official Q3 holdings parsed, NAV ratios and industry totals verified')
