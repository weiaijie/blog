"""Immutable-source probe. Refuse to overwrite any existing response/index."""
import urllib.request,urllib.error,json,datetime,hashlib,concurrent.futures,pathlib,time
BASE=pathlib.Path(__file__).parent
jobs=[('sse_fees', 'https://www.sse.com.cn/services/tradingservice/charge/ssecharge/'), ('tax_2002_128', 'https://fgk.chinatax.gov.cn/zcfgk/c102416/c5202818/content.html'), ('tax_2002_128_gd', 'https://guangdong.chinatax.gov.cn/gdsw/grsdsgg_hmqsc_pyzbsc_zjtz/2021-08/31/content_ba332d505b274cd5bac5ceab045542dc.shtml'), ('csrc_etf_tax', 'https://www.csrc.gov.cn/qinghai/c105501/c7422297/content.shtml'), ('broker_fees_boc', 'https://www.bocichina.com/main/a/20240627/493318.shtml'), ('sse_publicdata', 'https://www.sse.com.cn/market/publicdata/'), ('sse_market_trend', 'https://www.sse.com.cn/market/trend/'), ('prospectus_510300', 'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-08-13/510300_20260813_FPSL.pdf'), ('prospectus_511010', 'https://www.sse.com.cn/disclosure/fund/announcement/c/new/2026-09-21/511010_20260921_4HQ6.pdf')]
def run(job):
 name,url=job;p=BASE/(name+'.body')
 if p.exists():raise FileExistsError(p)
 r={'name':name,'url':url,'requested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};t=time.monotonic()
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.sse.com.cn/' if 'sse.com.cn' in url else 'https://finance.sina.com.cn/'})
  with urllib.request.urlopen(req,timeout=25) as resp:body=resp.read();r.update(status=resp.status,content_type=resp.headers.get('Content-Type'),final_url=resp.url)
 except urllib.error.HTTPError as e:body=e.read();r.update(status=e.code,error=str(e))
 except Exception as e:body=b'';r.update(error=type(e).__name__+': '+str(e))
 r.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),elapsed_seconds=round(time.monotonic()-t,2));p.write_bytes(body)
 return r
if __name__=='__main__':
 if (BASE/'requests.json').exists():raise FileExistsError('Use a new timestamped snapshot directory')
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:results=list(ex.map(run,jobs))
 (BASE/'requests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 for r in results:print(r['name'],r.get('status'),r.get('error',''),r['bytes'])
