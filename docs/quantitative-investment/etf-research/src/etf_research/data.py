"""Fail-closed loader for the exact audited snapshots, with prefix-only accessors."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
import hashlib,json,re
from .accounting import Dividend,money

SNAPSHOTS=('2026-11-02','2026-11-03-official-01','2026-11-03-official-02','2026-11-03-market-03')
SYMBOLS=('510300','511010')


def verify_manifest(folder):
    manifest=json.loads((folder/'manifest.json').read_text())
    for name,expected in manifest.items():
        path=folder/name
        if not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError('Manifest path escapes snapshot')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Snapshot hash mismatch: '+str(path))
    return manifest


@dataclass(frozen=True)
class RawBar:
    day: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    price_mode: str='unadjusted'


@dataclass(frozen=True)
class Dataset:
    sessions: tuple
    bars: dict
    dividends: tuple
    provenance: dict

    def history_before_open(self,symbol,session):
        if session not in self.sessions:raise ValueError('Unknown session')
        return tuple(self.bars[symbol][d] for d in self.sessions if d<session)

    def events_known_before_open(self,session):
        if session not in self.sessions:raise ValueError('Unknown session')
        # Announcement intraday publication times are unknown: only previous dates.
        return tuple(e for e in self.dividends if e.announcement_date<session)


def load_dataset(snapshots, *, extended=False):
    root=Path(snapshots)
    names=SNAPSHOTS+('2026-11-04-expansion-07','2026-11-04-calendar-08') if extended else SNAPSHOTS
    manifests={name:verify_manifest(root/name) for name in names}
    calendar_snapshot='2026-11-04-calendar-08' if extended else '2026-11-03-market-03'
    calendar=json.loads((root/calendar_snapshot/'calendar.json').read_text())['dates']
    if calendar!=sorted(set(calendar)):raise ValueError('Duplicate/nonmonotonic calendar')
    allbars={};tencent={}
    provenance={'manifests_sha256':{name:hashlib.sha256((root/name/'manifest.json').read_bytes()).hexdigest() for name in names},'price_mode':'unadjusted','volume_loaded':False,'event_sources':[]}
    for symbol in SYMBOLS:
        s=(root/('2026-11-04-expansion-07' if extended else '2026-11-02')/f'sina_daily_{symbol}.body').read_text()
        rows=json.loads(s[s.index('([')+1:s.rindex(')')])
        days=[r['day'] for r in rows]
        expected=[d for d in calendar if days[0]<=d<=days[-1]] if extended else calendar
        if days!=sorted(set(days)) or days!=expected:raise ValueError('Price/calendar mismatch')
        bars={}
        for r in rows:
            day=date.fromisoformat(r['day']);v={k:money(r[k],positive=True) for k in ['open','high','low','close']}
            if not v['low']<=min(v['open'],v['close'])<=max(v['open'],v['close'])<=v['high']:raise ValueError('Invalid OHLC')
            bars[day]=RawBar(day,**v)
        allbars[symbol]=bars
        if extended:
            files=['sohu_510300'] if symbol=='510300' else ['sohu_511010_2022','sohu_511010_2023','sohu_511010_recent']
            rows=[]
            for name in files:
                payload=json.loads((root/'2026-11-04-calendar-08'/(name+'.body')).read_text(encoding='gb18030'))
                if len(payload)!=1 or payload[0]['status']!=0:raise ValueError('Failed cross-source response')
                source=payload[0]['hq'];dates=[r[0] for r in source]
                if dates!=sorted(set(dates),reverse=True):raise ValueError('Malformed cross-source order')
                rows.extend([r[0],r[1],r[2],r[6],r[5]] for r in source if '2022-01-04'<=r[0]<='2026-10-30')
            rows.sort(key=lambda r:r[0])
        else:
            rows=json.loads((root/'2026-11-02'/f'tencent_raw_{symbol}.body').read_text())['data']['sh'+symbol]['day']
        days=[r[0] for r in rows]
        if days!=sorted(set(days)):raise ValueError('Duplicate/nonmonotonic cross-source dates')
        tencent[symbol]={date.fromisoformat(r[0]):r for r in rows if r[0]<=calendar[-1]}
    common=set.intersection(*(set(allbars[s]) & set(tencent[s]) for s in SYMBOLS))
    if not common:raise ValueError('No cross-verified prices')
    sessions=tuple(date.fromisoformat(d) for d in calendar if min(common)<=date.fromisoformat(d)<=max(common))
    if common!=set(sessions):raise ValueError('Gap in cross-source sample')
    for symbol in SYMBOLS:
        for d in sessions:
            for field,i in [('open',1),('close',2),('high',3),('low',4)]:
                if getattr(allbars[symbol][d],field)!=money(tencent[symbol][d][i],positive=True):raise ValueError('Cross-source OHLC mismatch')
    reconciliation=json.loads((root/'2026-11-03-official-02/reconciliation.json').read_text())
    dividends=[]
    for row in reconciliation['dividends']:
        record=date.fromisoformat(row['record_date']);pay=date.fromisoformat(row['pay_date'])
        if record<sessions[0]<=pay:raise ValueError('Initial entitlement requires explicit state')
        if not sessions[0]<=record<=sessions[-1]:continue
        ev=row['official_evidence']
        if row['official_status']!='verified' or not all(ev['field_checks'].get(k) is True for k in ['record_date','ex_date','pay_date','per_share']):raise ValueError('Unverified dividend')
        pdf=root/ev['snapshot']/ev['source_file']
        if not pdf.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe source path')
        if hashlib.sha256(pdf.read_bytes()).hexdigest()!=ev['pdf_sha256']:raise ValueError('Official evidence mismatch')
        for field in ['record_date','ex_date','pay_date']:
            if ev[field]!=row[field]:raise ValueError('Dividend evidence conflict')
        if money(ev['per_share'],positive=True)!=money(row['per_share'],positive=True):raise ValueError('Dividend amount conflict')
        txt=pdf.with_suffix('.txt').read_text()
        m=re.search(r'公告送出日期\s*[：:]\s*(\d{4})\s*年\s*(\d+)\s*月\s*(\d+)\s*日',txt)
        if not m:raise ValueError('Missing publication date')
        announce=date(*map(int,m.groups()))
        dividends.append(Dividend(row['symbol'],announce,record,date.fromisoformat(row['ex_date']),pay,money(row['per_share'],positive=True)))
        provenance['event_sources'].append({'symbol':row['symbol'],'ex_date':row['ex_date'],'announcement_date':str(announce),'pdf':str(pdf.relative_to(root)),'sha256':ev['pdf_sha256'],'url':ev['source_url']})
    if len({e.key for e in dividends})!=len(dividends):raise ValueError('Duplicate dividend')
    provenance.update(start=str(sessions[0]),end=str(sessions[-1]),session_count=len(sessions),event_count=len(dividends),excluded_current_or_unmatched_dates=True)
    if extended:provenance.update(cross_source='Sohu raw daily OHLC; exact fields only',historical_extension=True,not_forward_observations=True)
    return Dataset(sessions,{s:{d:allbars[s][d] for d in sessions} for s in SYMBOLS},tuple(sorted(dividends,key=lambda e:(e.ex_date,e.symbol))),provenance)
