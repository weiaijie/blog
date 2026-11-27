"""Public-source capture through curl; every attempt is retained, TLS stays on."""
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse
import hashlib,json,re,subprocess,tempfile,time

ROOT=Path(__file__).resolve().parents[2]
HOSTS={'quotes.sina.cn','q.stock.sohu.com','query.sse.com.cn','yunhq.sse.com.cn','www.sse.com.cn'}
TRANSIENT_EXIT={6,7,18,28,52,55,56,124}
TRANSIENT_HTTP={408,429,500,502,503,504}

def load_policy(path=None):
    c=json.loads((path or ROOT/'config/collection.json').read_text())
    if c['schema_version']!=1 or c['transport']!='curl' or c['address_family']!='ipv4':raise ValueError('Unsupported collection policy')
    if type(c['max_attempts']) is not int or not 1<=c['max_attempts']<=3:raise ValueError('Invalid attempt bound')
    if len(c['backoff_seconds'])!=c['max_attempts']-1:raise ValueError('Invalid backoff count')
    for key in ['connect_timeout_seconds','total_timeout_seconds','max_retry_after_seconds']:
        if type(c[key]) is not int or not 1<=c[key]<=60:raise ValueError('Invalid timeout bound')
    if any(type(x) is not int or not 0<=x<=30 for x in c['backoff_seconds']):raise ValueError('Invalid backoff')
    if type(c['max_response_bytes']) is not int or not 1<=c['max_response_bytes']<=10485760:raise ValueError('Invalid response bound')
    return c

@lru_cache(maxsize=1)
def client_version():
    value=subprocess.run(['curl','--version'],capture_output=True,text=True,check=True,timeout=5).stdout.splitlines()[0]
    match=re.match(r'curl (\d+)\.(\d+)\.(\d+)',value)
    if not match or tuple(map(int,match.groups()))<(7,70,0):raise ValueError('curl >= 7.70 is required for JSON metrics')
    return value

def retry_delay(row,policy,index):
    if index>=policy['max_attempts']-1:return None
    # Certificate failures (e.g. curl 60) and other permanent failures are not retried.
    if row['curl_exit'] not in TRANSIENT_EXIT and not (row['curl_exit']==0 and row.get('status') in TRANSIENT_HTTP):return None
    delay=policy['backoff_seconds'][index];requested=row.get('retry_after_seconds')
    if requested is not None:
        if requested>policy['max_retry_after_seconds']:return None
        delay=max(delay,requested)
    return delay

def capture_attempt(folder,name,url,policy):
    body=folder/(name+'.body');body.open('xb').close()
    version=client_version();started=time.monotonic();requested=datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(prefix='etf-http-header-') as temp:
        headers=Path(temp)/'headers'
        command=['curl','--disable','--silent','--show-error','--globoff','--ipv4','--noproxy','*',
            '--proto','=https','--connect-timeout',str(policy['connect_timeout_seconds']),
            '--max-time',str(policy['total_timeout_seconds']),'--max-filesize',str(policy['max_response_bytes']),
            '--user-agent','Mozilla/5.0','--referer','https://www.sse.com.cn/' if 'sse.com.cn' in url else 'https://finance.sina.com.cn/',
            '--output',str(body),'--dump-header',str(headers),'--write-out','%{json}','--url',url]
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=policy['total_timeout_seconds']+5)
            code=result.returncode;error=result.stderr.strip()
            try:metrics=json.loads(result.stdout)
            except ValueError:metrics={};error=error or 'Missing curl JSON metrics'
        except subprocess.TimeoutExpired:code=124;error='Subprocess deadline exceeded';metrics={}
        status=metrics.get('response_code',0)
        row=dict(name=name,url=url,requested_at_utc=requested.isoformat(),status=status,curl_exit=code,
            final_url=metrics.get('url_effective',url),content_type=metrics.get('content_type'),
            address_family='ipv4',certificate_verification_enabled=True,client_version=version,
            metrics={k:metrics.get(k) for k in ('remote_ip','http_version','ssl_verify_result','time_connect','time_appconnect','time_starttransfer','time_total')})
        if code or status!=200 or metrics.get('ssl_verify_result')!=0:row['error']=error or ('HTTP '+str(status) if status!=200 else 'Certificate verification metric missing/failed')
        if error and not code:row['diagnostic']=error
        if headers.exists():
            retry=re.findall(r'^Retry-After:\s*(.+)$',headers.read_text(encoding='iso-8859-1'),re.M|re.I)
            if retry:
                value=retry[-1].strip()
                try:seconds=float(value) if value.isdecimal() else (parsedate_to_datetime(value)-requested).total_seconds();row['retry_after_seconds']=max(0,seconds)
                except (ValueError,TypeError):row['retry_after_unparsed']=value
    row.update(bytes=body.stat().st_size,sha256=hashlib.sha256(body.read_bytes()).hexdigest(),elapsed_seconds=round(time.monotonic()-started,3))
    return row

def fetch(folder,name,url,policy=None,*,attempt_fn=capture_attempt,sleep=time.sleep):
    folder=Path(folder);policy=policy or load_policy();u=urlparse(url)
    if not re.fullmatch(r'[a-z0-9_]+',name):raise ValueError('Unsafe request name')
    if u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password:raise ValueError('Unsupported public-source URL')
    # Reserve the canonical output before any request; never overwrite earlier evidence.
    with (folder/(name+'.body')).open('xb') as selected:
        attempts=[]
        for i in range(policy['max_attempts']):
            row=attempt_fn(folder,name+'_attempt_'+str(i+1).zfill(2),url,policy);attempts.append(row)
            delay=retry_delay(row,policy,i)
            row['retry_delay_seconds']=delay
            if delay is None:break
            sleep(delay)
        last=attempts[-1];selected.write((folder/(last['name']+'.body')).read_bytes())
    return {**last,'name':name,'selected_attempt':last['name'],'attempts':attempts,'actual_requests':len(attempts)}

def save_transport(folder,policy):
    folder=Path(folder)
    with (folder/'transport_policy.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(policy,indent=2)+'\n')
    with (folder/'http_capture.py').open('xb') as f:f.write(Path(__file__).read_bytes())
