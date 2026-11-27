"""Read-only coverage shared by the observation workbench and Agent."""
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re

from run_research_observation import check_receipt
from collect_sse_research_day import CALENDAR_SHA
from etf_research.admission import completed_date, sessions_between
from etf_research.policy_events import TZ, instant
from etf_research.publication import read, sha

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


def expected_days(root, start, end):
    calendar = root/'data/snapshots/2026-11-04-calendar-08/calendar.json'
    if sha(calendar)!=CALENDAR_SHA:
        raise ValueError('Observation calendar digest mismatch')
    ranges = read(calendar)['holiday_ranges']
    for year in range(start.year,end.year+1):
        if str(year) not in ranges:
            boundary = date(year-1,12,31)
            return sessions_between(ranges,start,boundary), year
    return sessions_between(ranges,start,end),None


def archive_index(root, store, config, observed):
    log = root/'reports/research-observation'
    entries, errors = defaultdict(list), defaultdict(list)
    if not log.is_dir() or not (store/'snapshots').is_dir():
        raise FileNotFoundError('Observation ledger or archive unavailable')
    for folder in sorted((log/'runs').glob('*/*')):
        day = folder.parent.name
        try:
            parse_day(day)
            if not folder.is_dir() or folder.resolve()!=folder.absolute():
                continue
            receipt = log/'archives'/day/(folder.name+'.json')
            if not receipt.is_file():
                errors[day].append(dict(id=folder.name,status='pending_archive'))
                continue
            verified = check_receipt(folder,store,config,root=root)
            if instant(verified['archiveVerifiedAt'])>observed:
                raise ValueError('Archive verified time after observation')
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


def view_attempt(receipt, record):
    return dict(id=Path(receipt['attempt']).name,phase=receipt['phase'],
                scheduled=receipt['trigger'] is not None,startedAt=record['startedAt'],
                finishedAt=record['finishedAt'],archivedAt=receipt['archiveVerifiedAt'],
                qualified=receipt['forwardEligible'],archiveSha256=receipt['archive'],
                resultSha256=receipt['resultSha256'],
                sources=source_fields(record['coverage'],receipt['archiveVerifiedAt']),
                failedSources=sorted(record['errors']))


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
    sessions, unknown_year = expected_days(root,start,end)
    expected = {str(d) for d in sessions}
    entries,errors = archive_index(root,store,config,observed)
    qualified = [r for d in expected for r,_ in entries.get(d,()) if r['forwardEligible']]
    first = min(qualified,key=lambda row:instant(row['archiveVerifiedAt']),default=None)
    milestone = None
    if first is not None:
        first_day = instant(first['archiveVerifiedAt']).astimezone(TZ).date()
        milestone = dict(session=first['session'],date=str(first_day),at=first['archiveVerifiedAt'],
                         midtermOn=str(add_months(first_day,6)),finalOn=str(add_months(first_day,12)),
                         archiveSha256=first['archive'])
    if day is not None:
        session = parse_day(day)
        row = day_row(day,day in expected,entries,errors)
        if row['status']=='not_scheduled' and unknown_year and session.year>=unknown_year:
            row['status']='calendar_unknown'
        row['attempts'] = [view_attempt(*item) for item in reversed(entries.get(day,()))]
        return dict(schemaVersion=1,reportedAt=observed.isoformat(),session=row)
    limit = parse_day(before) if before is not None else date.max
    displayed = [d for d in sorted(expected | entries.keys() | errors.keys(),reverse=True)
                 if date.fromisoformat(d)<=limit]
    visible = displayed[:MAX_ROWS]
    return dict(schemaVersion=1,reportedAt=observed.isoformat(),calendarThrough=str(sessions[-1]) if sessions else None,
                calendarUnknownYear=unknown_year,firstQualifiedArchive=milestone,
                counts=dict(expected=len(expected),archived=sum(d in entries for d in expected),
                            qualified=len({row['session'] for row in qualified}),
                            missing=sum(d not in entries and d not in errors for d in expected)),
                nextBefore=displayed[MAX_ROWS] if len(displayed)>MAX_ROWS else None,
                sessions=[day_row(d,d in expected,entries,errors) for d in visible])
