"""Verify newly downloaded SSE dividend notices; carry forward first-batch evidence."""
from pathlib import Path
from decimal import Decimal
import hashlib,json,re
P=Path(__file__).parent
prior=json.loads((P.parent/'2026-11-03-official-01/reconciliation.json').read_text())
requests=json.loads((P/'requests.json').read_text())+json.loads((P/'older_requests.json').read_text())
def date(text,label):
 m=re.search(label+r'\s*(\d{4})\s*年\s*(\d+)\s*月\s*(\d+)\s*日',text)
 if not m:raise ValueError(label)
 return f'{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}'
checks=[]
for r in requests:
 name=r['name'];code=name[:6];pdf=P/(name+'.pdf')
 assert r['status']==200 and hashlib.sha256(pdf.read_bytes()).hexdigest()==r['sha256']
 s=(P/(name+'.txt')).read_text()
 m=re.search(r'本次分红方案[（(]单位[：:]元/10\s*份基金份额[）)]\s*([\d.]+)',s)
 method='table_row'
 if not m:
  # pdftotext layout for the 2013 announcement inserts the value between label lines.
  m=re.search(r'本次分红方案[（(]单位[：:]元/10\s*\n\s*([\d.]+)\s*\n份基金份额[）)]',s);method='wrapped_table_row'
 if not m:raise ValueError('Unrecognized amount layout: '+name)
 e={'record_date':date(s,'权益登记日'),'ex_date':date(s,'除息日'),'pay_date':date(s,'现金红利发放日'),'per_share':str(Decimal(m[1])/10),'per_10_shares':m[1],'source_url':r['url'],'pdf_sha256':r['sha256'],'source_file':name+'.pdf','snapshot':'2026-11-03-official-02','amount_parse_method':method}
 row=next(x for x in prior['dividends'] if x['symbol']==code and x['ex_date']==e['ex_date'])
 e['field_checks']={k:e[k]==row[k] for k in ['record_date','ex_date','pay_date']};e['field_checks']['per_share']=Decimal(e['per_share'])==Decimal(row['per_share'])
 assert all(e['field_checks'].values()),e
 assert row['official_status']=='pending','Duplicate verification: '+name
 row.update(official_status='verified',official_evidence=e);checks.append({'symbol':code,**e})
for row in prior['dividends']:
 row['official_evidence'].setdefault('snapshot','2026-11-03-official-01')
# Audit current complete API result pagination and known dividend-title coverage.
coverage={}
for code in ['510300','511010']:
 d=json.loads((P/(code+'_all_index.body')).read_text());rows=d['result'];page=d['pageHelp']
 assert not d.get('actionErrors') and not d.get('fieldErrors')
 assert page['pageCount']==1 and len(rows)==page['total']
 assert all(x['SECURITY_CODE']==code for x in rows)
 dividend_rows=[x for x in rows if '分红' in x['TITLE'] or '收益分配' in x['TITLE']]
 known={x['official_evidence']['source_url'] for x in prior['dividends'] if x['symbol']==code}
 found={'https://www.sse.com.cn'+x['URL'] for x in dividend_rows}
 assert found==known,{'missing':list(found-known),'unlisted':list(known-found)}
 coverage[code]={'all_notices_returned':len(rows),'api_total':page['total'],'page_count':page['pageCount'],'dividend_notices':len(dividend_rows),'matched_evidence_urls':True,'query_window':['2012-01-01','2026-11-03'],'limitation':'Current SSE catalogue plus title matching, not proof against upstream omission or unusually named notices.'}
prior.update(official_verified=sum(x['official_status']=='verified' for x in prior['dividends']),official_pending=sum(x['official_status']!='verified' for x in prior['dividends']),full_history_gate='BLOCKED_PENDING_PRICE_ADJUSTMENT_CALENDAR_AND_ACCOUNTING',dividend_gate='PASS_FOR_21_CATALOGUED_EVENTS',catalogue_coverage=coverage,newly_verified=len(checks))
(P/'reconciliation.json').write_text(json.dumps(prior,ensure_ascii=False,indent=2))
print(json.dumps({k:prior[k] for k in ['official_verified','official_pending','newly_verified','dividend_gate','full_history_gate','catalogue_coverage']},ensure_ascii=False))
