"""Dated PCF, exchange closing IOPV and explicitly time-bounded futures evidence."""
import csv
import hashlib
import io
import json
import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal as D
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from zoneinfo import ZoneInfo

from etf_research.data import verify_manifest
from market_evidence import ROOT, SNAPS

PREFIX = '2026-11-08-close-timing-0603'
SH = ZoneInfo('Asia/Shanghai')
NY = ZoneInfo('America/New_York')
PEAK, TROUGH = date(2024,12,16),date(2025,4,7)
BASE = ROOT/'reports/2026-11-08-nav-fx'
CLOSED = {date(2024,12,25),date(2025,1,1),date(2025,1,9),date(2025,1,20),date(2025,2,17)}


def folder(suffix):
    return SNAPS/(PREFIX+suffix)


def archived(name):
    path=BASE/(name+'.csv')
    expected=json.loads((BASE/'manifest.json').read_text())[path.relative_to(ROOT).as_posix()]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise ValueError('Archived research input changed: '+name)
    with path.open(encoding='utf8') as f:
        return list(csv.DictReader(f))


def cash_close(day):
    if not PEAK<=day<=TROUGH or day.weekday() >= 5 or day in CLOSED:
        return None
    return datetime.combine(day,time(13 if day==date(2024,12,24) else 16),NY)


def series(suffix,name,fields):
    path=folder(suffix)
    meta=next(r for r in json.loads((path/'requests.json').read_text()) if r['name']==name)
    if meta['status']!=200 or meta['exit_code'] or meta['url']!=meta['effective_url'] or not meta['url'].endswith('select='+fields):
        raise ValueError('Invalid exchange market query')
    data=json.loads((path/(name+'.body')).read_text(),parse_float=D)
    if data['code']!='513500' or not (len(data['kline'])==data['total']==data['end'] and data['begin']==0):
        raise ValueError('Incomplete exchange market series')
    out={}
    for stamp,*values in data['kline']:
        day=datetime.strptime(str(stamp),'%Y%m%d').date()
        if day in out or len(values)+1!=len(fields.split(',')):
            raise ValueError('Duplicate or malformed exchange day')
        out[day]=values
    return out


def pcf_records():
    out={}
    with ZipFile(folder('i')/'responses.zip') as z:
        for meta in json.loads((folder('i')/'requests.json').read_text()):
            stamp=meta['day']
            raw=z.read(stamp+'.body')
            if hashlib.sha256(raw).hexdigest()!=meta['sha256'] or len(raw)!=meta['bytes']:
                raise ValueError('PCF hash mismatch')
            if meta['status']!=200 or meta['exit_code']:
                continue
            if meta['url'].endswith('.xml'):
                root=ET.fromstring(raw)
                security,effective,vdate,nav=(root.findtext(k) for k in ('FundInstrumentID','TradingDay','PreTradingDay','NAV'))
            else:
                fields=dict(line.split('=',1) for line in raw.split(b'TAGTAG')[0].decode('gb18030').splitlines() if '=' in line)
                security,effective,vdate,nav=(fields[k] for k in ('Fundid1','TradingDay','PreTradingDay','NAV'))
            html=(folder('a')/'pcf_example.body' if stamp=='20250228' else folder('b')/f'pcf_{stamp}.body').read_text(encoding='utf8')
            prior=re.search(r'<b>(\d{4})年(\d\d)月(\d\d)日\s*信息内容</b>',html)
            value=re.search(r'基金份额净值\(单位：元\)</th>\s*<td>[￥¥]?([\d.]+)</td>',html)
            if (not prior or not value or security!='513500' or effective!=stamp or
                    ''.join(prior.groups())!=vdate or D(value[1])!=D(nav) or not vdate<stamp
                    or meta['url'].split('www.bosera.com')[-1] not in html):
                raise ValueError('Official PCF file vs rendered page mismatch '+stamp)
            day=datetime.strptime(stamp,'%Y%m%d').date()
            modified=parsedate_to_datetime(meta['last_modified']).astimezone(SH) if meta['last_modified'] else None
            out[day]=(datetime.strptime(vdate,'%Y%m%d').date(),D(nav),modified,meta['url'])
    return out


def futures():
    hourly={}
    for key in ('bridge','late25','26'):
        data=json.loads((folder('f')/('hour_'+key+'.body')).read_text(),parse_float=D)['chart']['result'][0]
        meta=data['meta']
        if (meta['symbol'],meta['exchangeName'],meta['dataGranularity'],meta['instrumentType'])!=('ES=F','CME','1h','FUTURE'):
            raise ValueError('Wrong futures series')
        prices=data['indicators']['quote'][0]['close']
        for ts,v in zip(data['timestamp'],prices,strict=True):
            if v is not None:
                end=datetime.fromtimestamp(ts,timezone.utc)+timedelta(hours=1)
                if end in hourly and hourly[end]!=D(v):
                    raise ValueError('Conflicting futures boundary')
                hourly[end]=D(v)
    samples={}
    for minutes in (1,3):
        selected={}
        for line in (folder('j')/f'rows_{minutes}m.jsonl').read_text().splitlines():
            stamp,op,high,low,close,*rest=next(csv.reader(io.StringIO(json.loads(line)['raw_line'])))
            opening=datetime.fromisoformat(stamp)
            if opening.tzinfo is None and minutes==1:
                opening=opening.replace(tzinfo=NY)
            if opening.utcoffset()!=opening.astimezone(NY).utcoffset():
                raise ValueError('Incorrect New York UTC offset')
            end=opening.astimezone(timezone.utc)+timedelta(minutes=minutes)
            if end in selected or not D(low)<=D(close)<=D(high):
                raise ValueError('Invalid ES bar')
            selected[end]=D(close)
        samples[minutes]=selected
    return hourly,samples


def audit_inputs():
    for suffix in 'abcdefghijk':
        verify_manifest(folder(suffix))
    rows=[r for r in archived('market') if r['symbol']=='513500']
    market={date.fromisoformat(r['date']):r for r in rows}
    dates=sorted(d for d,r in market.items() if D(r['premium_pct'])>5 or PEAK<=d<=TROUGH)
    main=series('c','dayk_select','date,close,iopv')
    reordered=series('d','dayk_control','date,iopv,close,preCloseIopv,time')
    pcf=pcf_records()
    hour,samples=futures()
    eid=json.loads((folder('k')/'eid_nav.body').read_text())
    if len(eid['aaData'])!=eid['iTotalRecords']:
        raise ValueError('Incomplete disclosure response')
    for r in eid['aaData']:
        d=date.fromisoformat(r['valuationDate'])
        if (r['code']!='513500' or (d in market and D(r['shareNetValue'])!=D(market[d]['nav_cny'])) or
                any(r.get(k) for k in ('uploadDatetime','uploadDate','importDatetime','reportSendDate'))):
            raise ValueError('Regulatory NAV or release evidence changed')
    result=[]
    for day in dates:
        cutoff=datetime.combine(day,time(15),SH)
        close,ind=main[day]
        ref,ctrl,_,tick_time=reordered[day]
        row=market[day]
        if close!=D(row['close_cny']) or close!=ctrl or ind!=ref or tick_time is not None:
            raise ValueError('Closing data or timestamp evidence changed '+str(day))
        nav=D(row['nav_cny'])
        val,pcfn,modified,url=pcf[day]
        if val in market and pcfn!=D(market[val]['nav_cny']):
            raise ValueError('PCF vs valuation history disagreement')
        eligible=[d for d,(_,_,m,_) in pcf.items() if d<=day and m and m<=cutoff]
        latest=max(eligible,key=lambda d:(pcf[d][0],d)) if eligible else None
        ref_day,known,_,_=pcf[latest] if latest else (None,)*4
        us=cash_close(day)
        h=hour.get(cutoff)
        m1,m3=(samples[m].get(cutoff) for m in (1,3))
        m=m3 if m3 is not None else m1
        cross='missing' if h is None and m is None else 'one_source'
        if h is not None and m is not None:
            cross='equal' if h==m else 'different'
        result.append(dict(date=day,high_expost=D(row['premium_pct'])>5,cn_close=cutoff.isoformat(),
            utc=cutoff.astimezone(timezone.utc).isoformat(),new_york=cutoff.astimezone(NY).isoformat(),
            close=close,expost_nav=nav,expost_premium_pct=D(row['premium_pct']),pcf_nav_date=val,
            pcf_nav=pcfn,pcf_last_modified=modified.isoformat() if modified else None,pcf_url=url,
            referenced_pcf_day=latest,documented_nav_date=ref_day,documented_nav=known,
            exact_first_publication=None,latest_across_all_channels=None,
            iopv=ind if ind and ind>0 else None,iopv_tick_time=None,
            close_iopv_premium_pct=(close/ind-1)*100 if ind and ind>0 else None,
            es_hour_start=(cutoff-timedelta(hours=1)).isoformat() if h is not None else None,
            es_hour_close=h,es_3m_close=m3,es_1m_close=m1,
            es_short_start=(cutoff-timedelta(minutes=3 if m3 is not None else 1)).isoformat() if m is not None else None,
            es_crosscheck=cross,expiry_verified=None,us_equity_close=us.isoformat() if us else None,
            es_hour_us=hour.get(us),es_3m_us=samples[3].get(us)))
    return result
