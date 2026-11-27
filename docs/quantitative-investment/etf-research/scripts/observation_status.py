"""Read-only coverage shared by the observation workbench and Agent."""
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from xml.etree import ElementTree

from run_research_observation import check_receipt
from observation_decision_status import FIRST_DECISION, decision_counts, decision_row, schedule
from observation_label_status import label_counts, label_row
from observation_forecast_status import forecast_counts, forecast_row, model_progress
from observation_evaluation_status import evaluation_view
from seal_observation_decision import first_archive
from etf_research.admission import completed_date, sessions_between
from etf_research.evidence_archive import object_path
from etf_research.exchange_calendar import calendar_at
from etf_research.observation_slots import scheduled_slot, trigger_instant
from etf_research.policy_events import TZ, instant
from etf_research.publication import read

DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
SYMBOLS = ('510300','511010')
MAX_ROWS = 30


def parse_day(value):
    if not DATE.fullmatch(value):
        raise ValueError('日期须为 YYYY-MM-DD。')
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError('日期无效。') from error


def production_paths():
    projects = Path.home()/'projects'
    return (Path(os.environ.get('ETF_OBSERVATION_ROOT', projects/'etf-research-observation')),
            Path(os.environ.get('ETF_OBSERVATION_ARCHIVE', projects/'etf-research-observation-archive')))


def expected_days(root, start, end, *, observed=None):
    ranges = calendar_at(root,observed if observed is not None else datetime.now(timezone.utc)).ranges
    for year in range(start.year,end.year+1):
        if str(year) not in ranges:
            boundary = date(year-1,12,31)
            return sessions_between(ranges,start,boundary), year
    return sessions_between(ranges,start,end),None


def archive_index(root, store, config, observed, *, days=None):
    log = root/'reports/research-observation'
    entries, errors = defaultdict(list), defaultdict(list)
    if not log.is_dir() or not (store/'snapshots').is_dir():
        raise FileNotFoundError('Observation ledger or archive unavailable')
    folders = ((log/'runs').glob('*/*') if days is None else
               (folder for day in days for folder in (log/'runs'/str(day)).glob('*')))
    for folder in sorted(folders):
        day = folder.parent.name
        try:
            parse_day(day)
            if not folder.is_dir() or folder.resolve()!=folder.absolute():
                continue
            started = folder/'started.json'
            if started.is_file() and instant(read(started)['startedAt'])>observed:
                continue
            receipt = log/'archives'/day/(folder.name+'.json')
            if not receipt.is_file() or instant(read(receipt)['archiveVerifiedAt'])>observed:
                errors[day].append(dict(id=folder.name,status='pending_archive'))
                continue
            verified = check_receipt(folder,store,config,root=root)
            if instant(verified['archiveVerifiedAt'])>observed:
                errors[day].append(dict(id=folder.name,status='pending_archive'))
                continue
            entries[day].append((verified,read(folder/'result.json')))
        except (OSError,ValueError,TypeError,KeyError):
            errors[day].append(dict(id=folder.name,status='unverified'))
    for records in entries.values():
        records.sort(key=lambda item:instant(item[0]['archiveVerifiedAt']))
    return entries,errors


def source_fields(coverage, archived_at):
    if coverage is None:
        return None
    policy, market = coverage['policy'], coverage['market']
    return dict(
        policy=dict(status=policy['status'], candidateCount=policy['candidateCount'],
                    reviewedCount=policy['signalEligibleCount'], issues=policy.get('issues',{}),
                    readyAt=archived_at if policy['status']=='archived' else None),
        etf={symbol:coverage['etf'][symbol] for symbol in SYMBOLS},
        market=dict(
            turnover=dict(status='verified' if market['turnoverCny'] is not None else 'unknown',
                          cny=market['turnoverCny'],readyAt=market['featureReadyAt'] if market['turnoverCny'] is not None else None),
            margin=dict(status='verified' if market['margin'] is not None else 'unknown',
                        balanceIdentity=market['margin']['balanceIdentity'] if market['margin'] is not None else None,
                        readyAt=market['featureReadyAt'] if market['margin'] is not None else None,
                        issues=market.get('issues',{}))))


def attempt_evidence(record, sources):
    trigger = record['trigger']
    manager = trigger.get('managerTimer') if trigger else None
    actual = trigger_instant(manager.get('lastTriggerUsec')) if manager else None
    slot = scheduled_slot(record) if manager else None
    state = ('manual' if trigger is None else 'manager_clock_unavailable' if manager is None else
             'scheduled_slot_verified' if slot is not None else 'scheduled_slot_unverified')
    gaps = None
    if sources is not None:
        required = [
            ('policy',sources['policy'],'archived'),
            *((symbol,fund,'verified_estimate') for symbol,fund in sources['etf'].items()),
            *((name,value,'verified') for name,value in sources['market'].items()),
        ]
        gaps = [name for name,item,wanted in required if item['status']!=wanted]
    return dict(timer=dict(state=state,plannedAt=slot.isoformat() if slot else None,
                           recordedTriggerAt=actual.astimezone(TZ).isoformat() if actual else None),
                missingSources=gaps)


def view_attempt(receipt, record):
    view = dict(id=Path(receipt['attempt']).name,phase=receipt['phase'],
                scheduled=receipt['trigger'] is not None,startedAt=record['startedAt'],
                finishedAt=record['finishedAt'],archivedAt=receipt['archiveVerifiedAt'],
                qualified=receipt['forwardEligible'],archiveSha256=receipt['archive'],
                resultSha256=receipt['resultSha256'],
                sources=source_fields(record['coverage'],receipt['archiveVerifiedAt']),
                failedSources=sorted(record['errors']))
    view['qualificationEvidence'] = attempt_evidence(record,view['sources'])
    if view['phase']=='complete' and view['scheduled'] and not view['qualified']:
        view['qualificationReason'] = 'scheduled_archive_not_eligible'
    return view


def archived_bytes(store, entry):
    body = object_path(store, entry['sha256']).read_bytes()
    if len(body)!=entry['bytes'] or sha256(body).hexdigest()!=entry['sha256']:
        raise ValueError('Archive object hash mismatch')
    return body


def returned_dates(body, source):
    if source=='guotai':
        pcf = ElementTree.fromstring(body)
        value = pcf.findtext('PreTradingDay','')
        return [parse_day(f'{value[:4]}-{value[4:6]}-{value[6:]}').isoformat()],1
    data = json.loads(body)
    rows, key = (data['dataList'],'date') if source=='huatai' else (
        data['result'],'STAT_DATE' if source=='shares' else 'opDate')
    if not isinstance(rows,list):
        raise ValueError('Source rows are not a list')
    for field in ('actionErrors','actionMessages','fieldErrors'):
        if data.get(field):
            raise ValueError('Exchange rejected the query')
    days = set()
    for row in rows:
        value = row[key]
        normalized = value if '-' in value else f'{value[:4]}-{value[4:6]}-{value[6:]}'
        days.add(parse_day(normalized).isoformat())
    return sorted(days),len(rows)


def request_evidence(store, files, prefix, record, source, name, expected):
    row = dict(source=source, request=name, expectedDates=expected, returnedDates=[],
               rowCount=None, receivedAt=None, url=None, sha256=None, httpStatus=None)
    if name is None:
        return dict(row,state='not_requested')
    try:
        entry = files[prefix+name+'.body']
        body = archived_bytes(store,entry)
        if (record['sha256']!=entry['sha256'] or record['bytes']!=entry['bytes']
                or record['name']!=name):
            raise ValueError('Request is not bound to the response')
        row.update(receivedAt=instant(record['receivedAt']).isoformat(), url=record['url'],
                   sha256=entry['sha256'], httpStatus=record['status'])
        if (record['status']!=200 or record['curl_exit'] or record.get('error')
                or record['final_url']!=record['url'] or record['metrics']['ssl_verify_result']!=0):
            return dict(row,state='response_unavailable')
        dates,count = returned_dates(body,source)
        state = ('empty_response' if not count else
                 'date_mismatch' if set(dates)!=set(expected) else 'dates_present')
        return dict(row,state=state,returnedDates=dates,rowCount=count)
    except (OSError,ValueError,TypeError,KeyError,AttributeError,ElementTree.ParseError):
        return dict(row,state='unverified')


def latest_source_evidence(store, receipt):
    identity = receipt['archive']
    attempt = receipt['attempt']
    try:
        raw = (store/'snapshots'/(identity+'.json')).read_bytes()
        if sha256(raw).hexdigest()!=identity:
            raise ValueError('Archive manifest changed')
        files = json.loads(raw)['files']
        rows = []
        for part in ('policy-etf-day','sse-research-day'):
            paths = [name for name in files if name.startswith(attempt+'/inputs/')
                     and name.endswith('-'+part+'/requests.json')]
            if not paths:
                continue
            request_path, = paths
            prefix = request_path.removesuffix('requests.json')
            run = json.loads(archived_bytes(store,files[prefix+'run.json']))
            day,prior = run['date'],run['previousDate']
            key = parse_day(day).strftime('%Y%m%d')
            requests = json.loads(archived_bytes(store,files[request_path]))
            records = {row['name']:row for row in requests}
            if len(records)!=len(requests) or day!=receipt['session']:
                raise ValueError('Invalid source request inventory')
            if part=='policy-etf-day':
                following = run['followingDate']
                pcf = 'nav_511010_'+parse_day(following).strftime('%Y%m%d') if following else None
                checks = [('shares','shares_'+key,[day]),('huatai','nav_510300',[prior,day]),
                          ('guotai',pcf,[day])]
            else:
                if run.get('schemaVersion',1) == 2:
                    details = [name for name in records if re.fullmatch(r'detail_'+key+r'_[1-9][0-9]*',name)]
                else:
                    details = [f'detail_{key}_{page}' for page in (1,2)]
                checks = [('margin','margin',[prior,day])]
                checks.extend(('margin_detail',name,[day]) for name in details)
            rows.extend(request_evidence(store,files,prefix,records.get(name,{}),source,name,dates)
                        for source,name,dates in checks)
        return dict(archiveSha256=identity,state='available' if rows else 'no_responses',requests=rows)
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        return dict(archiveSha256=identity,state='unverified',requests=[])


def day_row(day, planned, entries, errors):
    records = entries.get(day,())
    latest = view_attempt(*records[-1]) if records else None
    issues = errors.get(day,[])
    qualified = any(receipt['forwardEligible'] for receipt,_ in records)
    if qualified:
        status = 'qualified'
    elif latest:
        status = latest['phase']
    elif issues:
        status = 'unverified' if any(row['status']=='unverified' for row in issues) else 'pending_archive'
    else:
        status = 'missing' if planned else 'not_scheduled'
    return dict(day=day,expected=planned,status=status,archivedAttempts=len(records),
                latest=latest, issues=issues)


def add_months(start, months):
    total = start.month-1+months
    year,month = start.year+total//12,total%12+1
    return date(year,month,min(start.day,monthrange(year,month)[1]))


def report(root, store, *, day=None, before=None, observed=None):
    root,store = root.resolve(),store.resolve()
    config = read(root/'config/research_observation.json')
    start = parse_day(config['observationEarliestDate'])
    observed = datetime.now(timezone.utc) if observed is None else observed
    end = completed_date(observed)
    sessions, unknown_year = expected_days(root,start,end,observed=observed)
    expected = {str(d) for d in sessions}
    today = observed.astimezone(TZ).date()
    origin = first_archive(root,store,observed)
    requested_day = day
    planned, decision_unknown_year = expected_days(root,FIRST_DECISION,today,observed=observed)
    decisions = {day.isoformat(): decision_row(root,store,day,observed,planned=True)
                 for day in planned if day.isoformat()==requested_day or requested_day is None}
    labels = {key: label_row(root,store,date.fromisoformat(key),observed,decision,details=key==requested_day)
              for key,decision in decisions.items() if decision['status']=='eligible_inputs'}
    model_cache = {}
    forecasts = {key: forecast_row(root,store,date.fromisoformat(key),observed,origin,decision,
                                   details=key==requested_day,models=model_cache)
                 for key,decision in decisions.items()} if origin is not None else {}
    upcoming, _ = expected_days(root,max(today,FIRST_DECISION),today+timedelta(days=30),observed=observed)
    next_decision = next((row for day in upcoming if instant((row := schedule(day))['deadline'])>observed),None)

    def with_decision(row):
        day = date.fromisoformat(row['day'])
        decision = decisions.get(row['day'])
        if decision is None:
            forecast_calendar, unknown = expected_days(root,max(FIRST_DECISION,day),day,observed=observed)
            decision = decision_row(root,store,day,observed,planned=bool(forecast_calendar),calendar_unknown=bool(unknown))
        if day==today and decision['scheduledAt'] and row['status']=='not_scheduled':
            row['status'] = 'awaiting_market_close'
        row['decision'] = decision if row['day']==requested_day else {k:v for k,v in decision.items() if k!='attempts'}
        label = labels.get(row['day'])
        if label is None:
            label = label_row(root,store,day,observed,decision,details=row['day']==requested_day)
        row['label'] = label if row['day']==requested_day else {k:v for k,v in label.items() if k!='attempts'}
        forecast = forecasts.get(row['day'])
        if forecast is None:
            forecast = forecast_row(root,store,day,observed,origin,decision,
                                    details=row['day']==requested_day,models=model_cache)
        row['forecast'] = forecast if row['day']==requested_day else {k:v for k,v in forecast.items() if k!='attempts'}
        if row['day']==requested_day:
            end_of_day = instant(forecast['deadline']) if forecast['deadline'] else datetime.combine(day,time.max,TZ)
            model_at = min(observed,end_of_day)
            known_origin = origin if origin and instant(origin['archiveVerifiedAt'])<=model_at else None
            row['modelProgress'] = model_progress(root,store,known_origin,model_at)
        return row

    entries,errors = archive_index(root,store,config,observed)
    qualified = [r for d in expected for r,_ in entries.get(d,()) if r['forwardEligible']]
    milestone = None
    if origin is not None:
        first_day = date.fromisoformat(origin['date'])
        milestone = dict(session=Path(origin['receiptPath']).parent.name,date=str(first_day),
                         at=origin['archiveVerifiedAt'],midtermOn=str(add_months(first_day,6)),
                         finalOn=str(add_months(first_day,12)),archiveSha256=origin['archiveSha256'])
    if day is not None:
        session = parse_day(day)
        row = day_row(day,day in expected,entries,errors)
        if row['status']=='not_scheduled' and unknown_year and session.year>=unknown_year:
            row['status']='calendar_unknown'
        row['attempts'] = [view_attempt(*item) for item in reversed(entries.get(day,()))]
        row['latestSourceEvidence'] = latest_source_evidence(store,entries[day][-1][0]) if entries.get(day) else None
        return dict(schemaVersion=1,reportedAt=observed.isoformat(),session=with_decision(row))
    limit = parse_day(before) if before is not None else date.max
    displayed = [d for d in sorted(expected | entries.keys() | errors.keys() | decisions.keys(),reverse=True)
                 if date.fromisoformat(d)<=limit]
    visible = displayed[:MAX_ROWS]
    return dict(schemaVersion=1,reportedAt=observed.isoformat(),calendarThrough=str(sessions[-1]) if sessions else None,
                calendarUnknownYear=unknown_year or decision_unknown_year,firstQualifiedArchive=milestone,
                decisionCounts=decision_counts(decisions.values(),observed),
                labelCounts=label_counts(labels.values(),observed),
                modelProgress=model_progress(root,store,origin,observed),
                forecastCounts=forecast_counts(forecasts.values(),observed),
                evaluation=evaluation_view(root,store,observed,origin),
                nextDecision=next_decision,
                counts=dict(expected=len(expected),archived=sum(d in entries for d in expected),
                            qualified=len({row['session'] for row in qualified}),
                            missing=sum(d not in entries and d not in errors for d in expected)),
                nextBefore=displayed[MAX_ROWS] if len(displayed)>MAX_ROWS else None,
                sessions=[with_decision(day_row(d,d in expected,entries,errors)) for d in visible])
