import urllib.request,urllib.error,json,datetime,hashlib,concurrent.futures,pathlib,time
BASE=pathlib.Path(__file__).parent
jobs=[]
for code in ['510300','511010']:
 jobs += [(f'sina_daily_{code}',f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol=sh{code}&scale=240&ma=no&datalen=1023'),(f'sina_history_{code}',f'https://finance.sina.com.cn/realstock/company/sh{code}/hisdata/klc_kl.js'),(f'sina_hfq_{code}',f'https://finance.sina.com.cn/realstock/company/sh{code}/hfq.js'),(f'tencent_daily_{code}',f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh{code},day,2024-01-01,2026-11-02,640,qfq'),(f'eastmoney_dividend_{code}',f'https://fundf10.eastmoney.com/fhsp_{code}.html'),(f'sina_dividend_{code}',f'https://stock.finance.sina.com.cn/fundInfo/view/FundInfo_JJJZ.php?symbol={code}')]
 for adj in [0,1,2]:
  jobs.append((f'eastmoney_daily_fqt{adj}_{code}',f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.{code}&klt=101&fqt={adj}&beg=20240101&end=20261102&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'))
jobs += [('sse_calendar','https://www.sse.com.cn/services/tradingservice/tradingcalendar/'),('szse_calendar','https://www.szse.cn/marketServices/deal/')]
def run(job):
 name,url=job;r={'name':name,'url':url,'requested_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};t=time.monotonic()
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://finance.sina.com.cn/' if 'sina' in url else 'https://www.eastmoney.com/'})
  with urllib.request.urlopen(req,timeout=25) as resp:
   body=resp.read();r.update(status=resp.status,content_type=resp.headers.get('Content-Type'),final_url=resp.url)
 except urllib.error.HTTPError as e:
  body=e.read();r.update(status=e.code,error=str(e))
 except Exception as e:
  body=b'';r.update(error=type(e).__name__+': '+str(e))
 r.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),elapsed_seconds=round(time.monotonic()-t,2))
 (BASE/(name+'.body')).write_bytes(body)
 try:r['preview']=body.decode('utf-8')[:220]
 except UnicodeDecodeError:r['preview']=body.decode('gb18030',errors='replace')[:220]
 return r
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: results=list(ex.map(run,jobs))
 (BASE/'requests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 for r in results: print(r['name'],r.get('status'),r.get('error',''),r['bytes'],repr(r['preview'][:100]))
