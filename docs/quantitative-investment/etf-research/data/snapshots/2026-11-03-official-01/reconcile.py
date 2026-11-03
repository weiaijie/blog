"""Reconcile six original SSE dividend notices with the preserved supplier snapshot."""
from pathlib import Path
import json,re,hashlib
from decimal import Decimal
P=Path(__file__).parent
# In the repository this directory is data/snapshots/<timestamp>.
old=P.parent/'2026-11-02'/'validation.json'
if not old.exists():raise SystemExit('Place this folder beside the preserved 2026-11-02 snapshot before running.')
prior=json.loads(old.read_text());requests=json.loads((P/'requests.json').read_text())+json.loads((P/'extra_requests.json').read_text())
lookup={r['name']:r for r in requests};verified={}
def date(s,label):
 m=re.search(label+r'\s*(\d{4})\s*年\s*(\d+)\s*月\s*(\d+)\s*日',s)
 if not m:raise ValueError(label)
 return f'{int(m[1]):04}-{int(m[2]):02}-{int(m[3]):02}'
for name in ['510300_20250611','510300_20260112','511010_20250918','511010_20251223','511010_20260320','511010_20260622']:
 s=(P/(name+'.txt')).read_text();code=name[:6]
 assert lookup[name]['status']==200
 assert hashlib.sha256((P/(name+'.pdf')).read_bytes()).hexdigest()==lookup[name]['sha256']
 m=re.search(r'本次分红方案[（(]单位[：:]元/10\s*份基金份额[）)]\s*([\d.]+)',s)
 if not m:raise ValueError('amount '+name)
 event={'record_date':date(s,'权益登记日'),'ex_date':date(s,'除息日'),'pay_date':date(s,'现金红利发放日'),'per_share':str(Decimal(m[1])/10),'per_10_shares':m[1],'source_url':lookup[name]['url'],'pdf_sha256':lookup[name]['sha256'],'source_file':name+'.pdf'}
 supplied=next(e for e in prior[code]['dividend_events'] if e['ex_date']==event['ex_date'])
 event['field_checks']={k:event[k]==supplied[k] for k in ['record_date','ex_date','pay_date']}
 event['field_checks']['per_share']=Decimal(event['per_share'])==Decimal(supplied['per_share'])
 assert all(event['field_checks'].values()),event
 verified[(code,event['ex_date'])]=event
ledger=[]
for code in prior:
 for e in prior[code]['dividend_events']:
  key=(code,e['ex_date']);v=verified.get(key)
  ledger.append({'symbol':code,**e,'official_status':'verified' if v else 'pending','official_evidence':v})
splits=[]
for code,name,day,ratio in [('510300','510300_2025_report','2012-05-11','0.37094933'),('511010','511010_2013_report','2013-03-05','0.01')]:
 s=(P/(name+'.txt')).read_text();assert re.search(r'折算比例为\s*'+re.escape(ratio),s)
 splits.append({'symbol':code,'conversion_date':day,'new_units_per_old_unit':ratio,'source_url':lookup[name]['url'],'pdf_sha256':lookup[name]['sha256'],'source_file':name+'.pdf','status':'verified_in_fund_report','scope':'initial subscription unit conversion; do not reapply to later listed market prices'})
result={'official_verified':len(verified),'supplier_events':len(ledger),'official_pending':len(ledger)-len(verified),'all_verified_fields_match':True,'full_history_gate':'BLOCKED_PENDING_OFFICIAL_EVENTS','dividends':ledger,'initial_unit_conversions':splits}
(P/'reconciliation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['dividends','initial_unit_conversions']},ensure_ascii=False))
