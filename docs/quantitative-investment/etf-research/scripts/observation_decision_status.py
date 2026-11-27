"""Read the same archived decision receipts for the workbench and Agent."""
from datetime import date, datetime

from etf_research.policy_events import TZ, instant
from etf_research.publication import read, sha
from etf_research.observation_decision_receipt import DECISIONS, START, deadline, verify_decision

FIRST_DECISION = date(2026, 11, 30)
SEALED_INPUT = {'eligible_inputs', 'missing_inputs', 'study_origin_pending'}


def schedule(day):
    return dict(scheduledAt=datetime.combine(day,START,TZ).isoformat(),deadline=deadline(day).isoformat())


def decision_row(root, store, day, observed, *, planned, calendar_unknown=False):
    if not planned:
        state = 'calendar_unknown' if calendar_unknown else 'prelaunch' if day<FIRST_DECISION else 'not_scheduled'
        return dict(status=state, scheduledAt=None, deadline=None, attempts=[])
    cutoff = deadline(day)
    attempts = []
    for folder in sorted((root/DECISIONS/day.isoformat()).glob('*')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        receipt = folder/'receipt.json'
        payload = folder/'records/decision.json'
        try:
            record = read(payload) if payload.is_file() else None
            if record and instant(record['startedAt'])>observed:
                continue
            if not receipt.is_file() or instant(read(receipt)['archiveVerifiedAt'])>observed:
                state = 'pending_archive' if observed<cutoff else 'incomplete'
                attempts.append(dict(id=folder.name,status=state))
                continue
            verified = verify_decision(root,store,folder,observed=observed)
            inputs_file = folder/'records/inputs.json'
            if inputs_file.is_file() and sha(inputs_file)!=record['inputSha256']:
                raise ValueError('Decision inputs differ from receipt')
            gaps = read(inputs_file)['gaps'] if inputs_file.is_file() else {}
            reasons = {key: value.get('reason') if isinstance(value,dict) else value for key,value in gaps.items()}
            attempts.append(dict(id=folder.name,status=verified['status'],startedAt=record['startedAt'],
                archivedAt=verified['archiveVerifiedAt'],archiveSha256=verified['archiveSha256'],
                availableVariants=verified['availableVariants'],featureGaps=reasons,
                forecastProduced=verified['forecastProduced']))
        except (OSError, ValueError, KeyError, TypeError, ArithmeticError):
            attempts.append(dict(id=folder.name,status='unverified'))
    verified = [row for row in attempts if 'archivedAt' in row]
    accepted = min((row for row in verified if row['status'] in SEALED_INPUT),
                   key=lambda row: instant(row['archivedAt']),default=None)
    latest = accepted or max(verified,key=lambda row: instant(row['archivedAt']),default=None)
    if latest is None and attempts:
        latest = attempts[-1]
    state = latest['status'] if latest else 'missing' if observed>=cutoff else 'pending'
    return dict(status=state,**schedule(day),latest=latest,attempts=attempts)


def decision_counts(rows, observed):
    due = [row for row in rows if instant(row['deadline'])<=observed]
    return dict(expected=len(due),sealedOnTime=sum(row['status'] in SEALED_INPUT for row in due),
                eligibleInputDays=sum(row['status']=='eligible_inputs' for row in due),
                gaps=sum(row['status'] not in SEALED_INPUT for row in due))
