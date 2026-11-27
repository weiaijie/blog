"""Verify immutable independent ETF decision receipts without running feature assembly."""
from datetime import date, datetime, time, timezone

from .evidence_archive import verify as verify_archive
from .observation_experiment import DECISION_TIME
from .observation_slots import manager_activation, trigger_instant
from .policy_events import TZ, instant
from .publication import read, sha, verify_bundle

TIMER = 'etf-research-decision.timer'
START = time(8, 52)
DECISIONS = 'reports/research-decisions'
PROBES = 'reports/research-decision-probes'


def deadline(day):
    return datetime.combine(day,DECISION_TIME,TZ)


def current_slot(trigger, day, started):
    if not trigger or trigger['unit']!=TIMER:
        return False
    activated = (manager_activation(trigger,TIMER,(START,),started) if 'managerTimer' in trigger
                 else trigger_instant(trigger.get('timerRealtimeUsec')))
    return activated is not None and datetime.combine(day,START,TZ)<=activated<=started<=deadline(day)


def decision_status(record, ready_at):
    if record['mode']=='probe':
        return 'validation_only'
    day = date.fromisoformat(record['entryDay'])
    started = instant(record['startedAt'])
    finished = instant(record['finishedAt'])
    if not current_slot(record['trigger'],day,started) or not started<=finished<=ready_at<=deadline(day):
        return 'missed_deadline'
    if record['failure'] is not None:
        return 'failed'
    origin = record['studyOrigin']
    if origin is None or not instant(origin['archiveVerifiedAt'])<=started or record['entryDay']<origin['date']:
        return 'study_origin_pending'
    if not record['availableVariants']['baseline']:
        return 'missing_inputs'
    return 'eligible_inputs'


def verify_decision(root, store, folder, *, observed=None):
    observed = datetime.now(timezone.utc) if observed is None else observed
    root,store,folder = root.resolve(),store.resolve(),folder.resolve()
    records = folder/'records'
    verify_bundle(records)
    receipt = read(folder/'receipt.json')
    record = read(records/'decision.json')
    archived = verify_archive(store, receipt['archiveSha256'])
    sealed_at = instant(receipt['archiveVerifiedAt'])
    relative = records.relative_to(root).as_posix()
    manifest = sha(records/'manifest.json')
    archive_entries = archived['files']
    source_hashes = record['codeSha256']
    files = {p.relative_to(root).as_posix():sha(p) for p in records.iterdir()}
    expected_root = PROBES if record['mode']=='probe' else DECISIONS
    day = date.fromisoformat(record['entryDay'])
    if (folder.parent.parent!=root/expected_root or
            record['deadline']!=deadline(day).isoformat() or
            record['mode']=='scheduled' and (record['trigger'] or {}).get('invocationId')!=folder.name or
            receipt['recordManifestSha256']!=manifest or
            receipt['decisionPath']!=folder.relative_to(root).as_posix() or
            record['entryDay']!=folder.parent.name or
            not instant(record['startedAt'])<=instant(record['finishedAt'])
                <=instant(archived['created_at_utc'])<=sealed_at<=observed or
            receipt['status']!=decision_status(record,sealed_at) or
            record['inputSha256']!=files.get(relative+'/inputs.json') or
            set(archive_entries)!=set(files)|set(source_hashes) or
            any(archive_entries[path]['sha256']!=digest for path,digest in {**files,**source_hashes}.items())):
        raise ValueError('Decision receipt, record or archive does not match')
    return dict(receipt,entryDay=record['entryDay'],availableVariants=record['availableVariants'],
                failure=record['failure'],studyOrigin=record['studyOrigin'],forecastProduced=False)
