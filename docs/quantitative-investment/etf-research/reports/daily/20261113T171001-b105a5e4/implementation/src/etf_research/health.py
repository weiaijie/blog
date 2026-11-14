"""Calendar-aware operational health; no market requests or account writes."""
from datetime import date, datetime, time, timedelta
from .admission import TZ, completed_date, sessions_between

SLOTS = (time(16, 10), time(16, 40), time(17, 10))


def evaluate(now, ranges, active, operation, scheduler, reviews=()):
    if now.tzinfo is None:
        raise ValueError('Timezone-aware health time required')
    now = now.astimezone(TZ)
    issues = []
    result = dict(schema_version=1, checked_at=now.isoformat(), account_through=active['as_of'],
                  scheduler=scheduler, issues=issues, review_queue=list(reviews), report_only=True)
    try:
        # Check today's year even before the close: a missing calendar is not a holiday.
        today_open = bool(sessions_between(ranges, now.date(), now.date()))
        days = sessions_between(ranges, date(2026, 11, 5), completed_date(now))
        target = days[-1] if days else None
    except ValueError:
        result.update(state='calendar_missing', actionable=True, expected_through=None)
        issues.append('calendar_missing')
        return result
    result['expected_through'] = str(target) if target else None
    account = date.fromisoformat(active['as_of'])
    if target and account > target:
        issues.append('account_ahead_of_completed_calendar')
    for key, expected in [('timer_enabled', 'enabled'), ('timer_active', 'active'), ('linger', 'yes')]:
        if scheduler.get(key) != expected:
            issues.append('scheduler_' + key)
    started = datetime.fromisoformat(operation['started_at_utc']) if operation else None
    if not operation: issues.append('no_runtime_observation')
    if started and (started.tzinfo is None or started > now + timedelta(seconds=60)):
        raise ValueError('Invalid operation timestamp')
    if operation and operation.get('phase') == 'running':
        if now - started > timedelta(minutes=16):
            issues.append('stalled_run')
    elif operation and operation.get('phase') == 'failed':
        issues.append('run_failed')
        if (operation.get('result') or {}).get('error_type') == 'CatalogChanged':
            issues.append('notice_review_required')
    if reviews:
        issues.append('notice_review_required' if any(r['pending_changes'] for r in reviews) else 'reviewed_but_admission_blocked')
    # Each due slot has a 20-minute grace; an old success cannot hide a stopped job.
    due = [datetime.combine(now.date(), slot, TZ) for slot in SLOTS
           if today_open and datetime.combine(now.date(), slot, TZ) + timedelta(minutes=20) <= now]
    if due and (not started or started < due[-1] or operation.get('mode') != 'scheduled'):
        issues.append('missed_schedule')
    behind = target is not None and account < target
    first_due = datetime.combine(target, SLOTS[0], TZ) + timedelta(minutes=20) if target else None
    if behind and now >= first_due:
        issues.append('account_stale')
    if issues:
        state = issues[0]
    elif operation and operation.get('phase') == 'running':
        state = 'running'
    elif not today_open:
        state = 'market_closed'
    elif now.time() < time(16):
        state = 'before_collection_window'
    elif behind:
        state = 'awaiting_scheduled_collection'
    else:
        state = 'current'
    result.update(state=state, actionable=bool(issues), operation=operation.get('operation') if operation else None)
    return result
