"""Deterministic notice deltas. Risk hints never imply permission to admit data."""
import hashlib,json
from urllib.parse import urljoin,urlparse

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def official_notice_url(path):
 parsed=urlparse(path)
 if parsed.scheme or parsed.netloc or not path.startswith('/disclosure/fund/announcement/') or '..' in path.split('/'):
  raise ValueError('Notice link is not an expected official fund-disclosure path')
 return urljoin('https://www.sse.com.cn',path)

def risk_hints(title):
 hints=[]
 for name,words in [('cash_distribution',['分红','收益分配']),('share_change',['折算','拆分','合并','份额调整']),('trading_or_fund_status',['停牌','复牌','暂停','终止','清盘','上市','转型'])]:
  if any(word in title for word in words):hints.append(name)
 return hints or ['unclassified_requires_full_text']

def diff_catalogs(current,previous):
 changes=[]
 for url in sorted(set(current)|set(previous)):
  before=previous.get(url);after=current.get(url)
  if before==after:continue
  kind='added' if before is None else 'removed' if after is None else 'modified'
  item={'kind':kind,'url':url,'before':before,'after':after,'risk_hints':sorted(set(risk_hints((before or {}).get('TITLE',''))+risk_hints((after or {}).get('TITLE','')))),'review_status':'pending','automatically_admissible':False}
  # Empty side is not itself an unclassified notice.
  item['risk_hints']=sorted(set(h for side in [before,after] if side for h in risk_hints(side['TITLE'])))
  item['change_id']=hashlib.sha256(canonical({k:item[k] for k in ['kind','url','before','after']}).encode()).hexdigest()
  changes.append(item)
 return changes

class CatalogChanged(ValueError):
 def __init__(self,changes):
  self.changes=changes
  counts={kind:sum(c['kind']==kind for c in changes) for kind in ['added','modified','removed']}
  super().__init__('Official catalog changed: '+canonical(counts)+'; full notice review required before price admission')
