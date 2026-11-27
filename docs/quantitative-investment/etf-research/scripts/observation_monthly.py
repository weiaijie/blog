"""Measure independent source coverage on the verified exchange calendar."""
from calendar import monthrange
from collections import Counter
from datetime import date, timedelta
import re

from observation_status import archive_index, expected_days, parse_day, view_attempt
from etf_research.admission import completed_date
from etf_research.observation_decision_receipt import deadline
from etf_research.policy_events import TZ, instant
from etf_research.publication import read

SOURCES = ('policy','510300','511010','turnover','margin')
AVAILABLE = dict(policy='archived',turnover='verified',margin='verified',
                 **{'510300':'verified_estimate','511010':'verified_estimate'})
LOG = 'reports/research-monthly-coverage'


def parse_month(value):
    if not re.fullmatch(r'\d{4}-\d{2}',value):
        raise ValueError('月份须为 YYYY-MM。')
    return parse_day(value+'-01')


def bounds(month):
    first = parse_month(month)
    return first,first.replace(day=monthrange(first.year,first.month)[1])


def source_record(attempt, key):
    sources = attempt['sources']
    if sources is None:
        return None
    if key == 'policy':
        return sources['policy']
    if key in sources['etf']:
        return sources['etf'][key]
    return sources['market'][key]


def availability(attempts, key, cutoff, observed):
    chosen = None
    for attempt in attempts:
        source = source_record(attempt,key)
        if source is None or source['status'] != AVAILABLE[key]:
            continue
        ready = source.get('featureReadyAt') or source.get('readyAt')
        if ready is None:
            continue
        when = max(instant(ready),instant(attempt['archivedAt']))
        if when <= observed and (chosen is None or when < chosen[0]):
            chosen = when,attempt
    if chosen is None:
        latest = source_record(attempts[-1],key) if attempts else None
        return dict(status='missing',readyAt=None,archiveSha256=None,
                    issues={} if latest is None else latest.get('issues',{}))
    when,attempt = chosen
    timing = 'cutoff_unknown' if cutoff is None else 'on_time' if when <= cutoff else 'late'
    return dict(status=timing,readyAt=when.isoformat(),archiveSha256=attempt['archiveSha256'],issues={})


def attempt_proof(attempt):
    fields = ('id','phase','archivedAt','qualified','archiveSha256','resultSha256','failedSources')
    return {key:attempt[key] for key in fields}


def gap_runs(rows, is_gap):
    gaps = []
    current = None
    for row in rows:
        if is_gap(row):
            if current is None:
                current = dict(start=row['day'],end=row['day'],sessions=1)
                gaps.append(current)
            else:
                current.update(end=row['day'],sessions=current['sessions']+1)
        else:
            current = None
    return gaps


def month_report(root, store, month, observed):
    """Aggregate frozen receipt metadata. Counts always refer to distinct exchange sessions."""
    month_start,month_end = bounds(month)
    config = read(root/'config/research_observation.json')
    coverage_start = max(month_start,parse_day(config['observationEarliestDate']))
    through = min(completed_date(observed),month_end)
    today = observed.astimezone(TZ).date()
    planned,unknown = expected_days(root,coverage_start,month_end)
    sessions = tuple(day for day in planned if day<=through)
    after,cutoff_unknown = expected_days(root,month_end+timedelta(days=1),month_end+timedelta(days=31))
    next_sessions = (*planned[1:],*after[:1])
    cutoffs = {day:deadline(next_day) for day,next_day in zip(planned,next_sessions)}
    close_after = cutoffs.get(planned[-1]) if planned else None
    state = 'before_launch' if coverage_start > month_end else (
        'calendar_unverified' if unknown or (today>month_end and planned and close_after is None) else
        'ready_to_archive' if today>month_end and close_after and observed>=close_after else 'open')
    if sessions:
        entries,errors = archive_index(root,store,config,observed,days=sessions)
    else:
        entries,errors = {},{}
    rows = []
    for day in sessions:
        key = str(day)
        records = entries.get(key,())
        all_attempts = [view_attempt(*entry) for entry in records]
        attempts = [attempt for attempt in all_attempts if attempt['scheduled']]
        manual = [attempt for attempt in all_attempts if not attempt['scheduled']]
        issues = errors.get(key,[])
        qualified = any(item['qualified'] for item in attempts)
        status = ('qualified' if qualified else attempts[-1]['phase'] if attempts else
                  'unverified' if any(issue['status']=='unverified' for issue in issues) else
                  'pending_archive' if issues else 'missing')
        cutoff = cutoffs.get(day)
        rows.append(dict(day=key,cutoffAt=cutoff.isoformat() if cutoff else None,
                         status=status,qualified=qualified,
                         attempts=[attempt_proof(item) for item in attempts],
                         manualAttempts=[attempt_proof(item) for item in manual],issues=issues,
                         sources={key:availability(attempts,key,cutoff,observed) for key in SOURCES}))
    result = {}
    for key in SOURCES:
        counts = Counter(row['sources'][key]['status'] for row in rows)
        gaps = gap_runs(rows,lambda row:row['sources'][key]['status']=='missing')
        result[key] = dict(available=len(rows)-counts['missing'],onTime=counts['on_time'],
                           late=counts['late'],cutoffUnknown=counts['cutoff_unknown'],
                           missing=counts['missing'],gaps=gaps)
    return dict(schemaVersion=1,month=month,asOf=observed.astimezone(TZ).isoformat(),
                state=state,calendarUnknownYear=unknown or (cutoff_unknown if planned and close_after is None else None),
                sealAfter=close_after.isoformat() if close_after else None,expected=len(rows),
                archived=sum(bool(row['attempts']) for row in rows),
                qualified=sum(row['qualified'] for row in rows),
                noScheduledArchive=sum(not row['attempts'] for row in rows),
                qualificationGaps=gap_runs(rows,lambda row:not row['qualified']),sources=result,days=rows)
