"""Create a new immutable notice-review packet; never approve market data."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,urllib.request,urllib.error,hashlib
from etf_research.notice_review import prepare_review

def main():
 p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--download-evidence',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[1]
 packet=prepare_review(root/'data/snapshots',a.snapshot)
 a.output.mkdir(parents=True,exist_ok=False)
 requests=[]
 if a.download_evidence:
  for item in packet['changes']:
   if item['kind']=='removed':continue # Disappearance never cancels a ledger event automatically.
   r={'change_id':item['change_id'],'url':item['official_url'],'requested_at_utc':datetime.now(timezone.utc).isoformat()}
   try:
    request=urllib.request.Request(r['url'],headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.sse.com.cn/'})
    with urllib.request.urlopen(request,timeout=25) as response:body=response.read();r.update(status=response.status,final_url=response.url)
   except urllib.error.HTTPError as e:body=e.read();r.update(status=e.code,error=str(e))
   except Exception as e:body=b'';r['error']=type(e).__name__+': '+str(e)
   name=item['change_id']+'.body';(a.output/name).write_bytes(body)
   r.update(file=name,sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),pdf_magic_valid=body.startswith(b'%PDF-'),reviewed=False);requests.append(r)
 (a.output/'packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
 (a.output/'evidence_requests.json').write_text(json.dumps(requests,ensure_ascii=False,indent=2)+'\n')
 lines=['# 公告变化审阅清单','','此文件不批准行情或事件入账。分类只是提示，必须读完整官方公告。撤下公告不等于取消已登记分红。','',f"候选快照：{packet['candidate_snapshot']}；状态：{packet['status']}；变化：{len(packet['changes'])}项。"]
 for item in packet['changes']:
  r=item['after'] or item['before'];lines+=['',f"## {item['symbol']} / {item['kind']} / {r['TITLE']}",f"- 官方链接：{item['official_url']}",f"- 变更指纹：{item['change_id']}",f"- 相关事项提示：{', '.join(item['risk_hints'])}",'- 审阅状态：待核对；不得仅凭标题自动更新分红或停复牌。']
 if not packet['changes']:lines+=['','本次取得的目录与基线相同；这不证明上游绝无遗漏，也不独立批准价格或前瞻收益。']
 (a.output/'REVIEW.md').write_text('\n'.join(lines)+'\n')
 manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(a.output.iterdir()) if f.is_file()};(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'status':packet['status'],'changes':len(packet['changes']),'evidence_requests':len(requests),'approves_prices_or_events':False}))
 if any(r.get('status')!=200 or not r['pdf_magic_valid'] for r in requests):raise SystemExit(2)
if __name__=='__main__':main()
