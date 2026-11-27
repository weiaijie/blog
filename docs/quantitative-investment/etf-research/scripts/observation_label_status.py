"""Share verified five-session label coverage with the workbench and Agent."""
from observation_labels import EVIDENCE_ERRORS, label_window
from seal_observation_labels import LOG, verified_label
from etf_research.observation_decision_receipt import DECISIONS
from etf_research.observation_experiment import label_floor
from etf_research.policy_events import instant
from etf_research.publication import read


def label_row(root, store, entry, observed, decision, *, details=False):
    waiting = dict(sessions=[],notBefore=None,readyAt=None,latest=None,attempts=[])
    if decision['status']!='eligible_inputs':
        return dict(waiting,status='decision_ineligible')
    try:
        window = label_window(root,entry,observed)
    except EVIDENCE_ERRORS:
        return dict(waiting,status='calendar_unverified')
    floor = label_floor(window)
    shape = dict(waiting,sessions=[day.isoformat() for day in window.sessions],notBefore=floor.isoformat())
    if observed<floor:
        return dict(shape,status='holding_period_incomplete')
    decision_attempt = decision['latest']
    attempts = []
    for folder in sorted((root/LOG/str(entry)).glob('*')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        path = folder/'receipt.json'
        try:
            if not path.is_file():
                attempts.append(dict(id=folder.name,status='pending_archive'))
                continue
            if instant(read(path)['archiveVerifiedAt'])>observed:
                continue
            receipt,payload = verified_label(root,store,folder,observed=observed)
            binding = payload['decision']
            expected = f'{DECISIONS}/{entry}/{decision_attempt["id"]}'
            if (binding['path']!=expected or binding['archiveSha256']!=decision_attempt['archiveSha256']
                    or binding['receiptSha256']!=decision_attempt['receiptSha256']
                    or payload['sessions']!=shape['sessions'] or payload['anchorDay']!=str(window.anchor)
                    or payload['lastSession']!=str(window.last) or instant(payload['notBefore'])!=floor):
                raise ValueError('Label belongs to a different decision or trading window')
            record = dict(id=folder.name,status=receipt['status'],archiveSha256=receipt['archiveSha256'],
                          archivedAt=receipt['archiveVerifiedAt'],readyAt=receipt['labelReadyAt'])
            if details:
                record.update(gaps=payload['gaps'],results=payload['labels'],opening=payload['opening'])
            attempts.append(record)
        except EVIDENCE_ERRORS:
            attempts.append(dict(id=folder.name,status='unverified'))
    verified = [row for row in attempts if 'archivedAt' in row]
    first = min((row for row in verified if row['status']=='evidence_complete'),
                key=lambda row:instant(row['readyAt']),default=None)
    latest = first or max(verified,key=lambda row:instant(row['archivedAt']),default=None)
    if latest is None and attempts:
        latest = attempts[-1]
    return dict(shape,status=latest['status'] if latest else 'mature_unsealed',
                latest=latest,attempts=attempts,readyAt=first['readyAt'] if first else None)


def label_counts(rows, observed):
    due = [row for row in rows if row['notBefore'] and instant(row['notBefore'])<=observed]
    ready = sum(row['status']=='evidence_complete' for row in due)
    return dict(due=len(due),ready=ready,gaps=len(due)-ready,
                holding=sum(row['status']=='holding_period_incomplete' for row in rows),
                unknownCalendar=sum(row['status']=='calendar_unverified' for row in rows))
