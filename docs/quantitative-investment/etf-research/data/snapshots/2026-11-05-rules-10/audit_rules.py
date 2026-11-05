"""Bind reviewed general-rule versions to official notices and attachments."""
from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,re
root=Path(__file__).parent
requests=[]
for p in sorted(root.glob('*requests.json')):requests+=json.loads(p.read_text())
byname={r['name']:r for r in requests}
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,s):self.parts.append(s)
def html(name):
 p=Text();p.feed((root/(name+'.body')).read_text());return ' '.join(p.parts)
assert '自2020年3月13日起实施' in html('sse_rules_2020')
assert '首只主板股票上市首日起施行' in html('sse_rules_2023')
assert '2026年7月6日起施行' in html('sse_rules_2026')
annual=(root/'sse_2023_events.txt').read_text();assert '4 月 10 日' in annual and '主板注册制首批企业上市仪式' in annual
versions=[]
for year,start,end,deferred in [('2020','2020-03-13','2023-04-10',3),('2023','2023-04-10','2026-07-06',4),('2026','2026-07-06',None,3)]:
 name='sse_rules_'+year+'_attachment_1';lines=(root/(name+'.txt')).read_text().splitlines();clauses={}
 nums={'round_trip':'3.1.5','buy_lot':'3.4.7' if year=='2020' else '3.3.8','price_tick':'3.4.11' if year=='2020' else '3.3.11','limit_formula':'3.4.13' if year=='2020' else '3.3.13','ex_reference':'4.3.2','ex_limit_base':'4.3.3'}
 for key,num in nums.items():
  matches=[i for i,l in enumerate(lines) if l.strip().startswith(num+' ') or l.strip().startswith(num+'　') or (key.startswith('ex_') and l.strip().startswith(num))]
  assert len(matches)==1,(year,key,matches)
  i=matches[0];j=next((j for j in range(i+1,len(lines)) if re.match(r'^\d+\.\d+\.\d+',lines[j].strip())),len(lines));excerpt='\n'.join(lines[i:j]).strip()
  clauses[key]={'clause':num,'text_file':name+'.txt','first_line':i+1,'text_sha256':hashlib.sha256(excerpt.encode()).hexdigest()}
 text='\n'.join(lines);assert '100股（份）' in text and '0.001' in text and '债券交易型开放式指数基金' in text and '10%' in text
 versions.append({'version':year,'effective_from':start,'superseded_from_exclusive':end,'notice_url':byname['sse_rules_'+year]['url'],'rules_url':byname[name]['url'],'rules_file':name+'.body','rules_sha256':hashlib.sha256((root/(name+'.body')).read_bytes()).hexdigest(),'deferred_file':'sse_rules_'+year+'_attachment_'+str(deferred)+'.txt','clauses':clauses})
report={'reviewed_on_shanghai':'2026-11-05','scope':'General rule evidence, not per-instrument daily reference prices, queue availability, tax opinion or complete historical simulation','versions':versions,'effective_2023_basis':['sse_rules_2023.body','sse_rules_2023_attachment_1.txt','sse_2023_events.body','sse_2023_events.txt'],'limitations':['Specific exceptions and issuer-adjusted ex references still need event/day evidence','No broker fee or full ETF tax conclusion','Odd-lot liquidation and deferred provisions are not implemented as full matching rules','Frozen protocol 9pct buffer and scenario costs unchanged'],'requests':len(requests),'status_counts':{str(status):sum(r.get('status')==status for r in requests) for status in sorted({r.get('status') for r in requests})}}
(root/'rule_versions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir()) if p.is_file() and p.name!='manifest.json'};(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'versions':[v['version'] for v in versions],'requests':len(requests),'statuses':report['status_counts']},ensure_ascii=False))
