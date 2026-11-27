"""Read calendar discovery and admission at one evidence cutoff."""
import re

from discover_exchange_calendar import ERRORS, LOG, TIMER, target_year, verify
from etf_research.evidence_archive import verify as verify_archive
from etf_research.exchange_calendar import REGISTRY, calendar_at
from etf_research.policy_events import instant
from etf_research.publication import read, sha


def parse_year(value):
    if not re.fullmatch(r'[0-9]{4}',value) or not 2000<=int(value)<=2100:
        raise ValueError('年份须为 2000–2100。')
    return int(value)


def scheduled_record(root,store,folder,year,observed,receipt):
    records = folder/'records'
    outcome = verify(records)
    started = read(records/'started.json')
    sealed = instant(receipt['archiveVerifiedAt'])
    identity = receipt['archiveSha256']
    archived = verify_archive(store,identity)
    trigger = receipt['trigger']
    path = folder.relative_to(root).as_posix()
    digest = sha(records/'manifest.json')
    if (receipt['schemaVersion']!=1 or receipt['path']!=path or started['year']!=year
            or outcome['year']!=year or receipt['year']!=year or receipt['status']!=outcome['status']
            or receipt['manifestSha256']!=digest
            or archived['files'][path+'/records/manifest.json']['sha256']!=digest
            or started.get('trigger')!=trigger or trigger['unit']!=TIMER
            or not re.fullmatch('[0-9a-f]{32}',trigger['invocationId'])
            or not instant(started['startedAt'])<=instant(outcome['checkedAt'])
            <=instant(archived['created_at_utc'])<=sealed<=observed):
        raise ValueError('Calendar timer receipt is not bound to its evidence')
    return dict(**outcome,archiveVerifiedAt=receipt['archiveVerifiedAt'],archiveSha256=identity,
                attempt=folder.name)


def scheduled(root,store,year,observed):
    items, issues = [], []
    for folder in sorted((root/LOG/str(year)).glob('*')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        try:
            started = instant(read(folder/'records/started.json')['startedAt'])
        except ERRORS:
            continue
        if started>observed:
            continue
        try:
            path = folder/'receipt.json'
            if not path.is_file():
                issues.append(dict(attempt=folder.name,state='pending_archive',startedAt=started.isoformat()))
                continue
            receipt = read(path)
            if instant(receipt['archiveVerifiedAt'])>observed:
                issues.append(dict(attempt=folder.name,state='pending_archive',startedAt=started.isoformat()))
                continue
            items.append(scheduled_record(root,store,folder,year,observed,receipt))
        except ERRORS:
            issues.append(dict(attempt=folder.name,state='unverified',startedAt=started.isoformat()))
    return items,issues


def manual(project,year,observed):
    items = []
    for folder in sorted((project/'data/snapshots').glob(f'*-exchange-calendar-discovery-{year}')):
        try:
            checked = instant(read(folder/'result.json')['checkedAt'])
            if checked>observed:
                continue
            outline = verify(folder)
            if outline['year']==year:
                items.append(dict(**outline,snapshot=folder.relative_to(project).as_posix(),
                                  manifestSha256=sha(folder/'manifest.json')))
        except ERRORS:
            continue
    return max(items,key=lambda item:instant(item['checkedAt']),default=None)


def calendar_report(project,root,store,observed,*,year=None):
    calendar = calendar_at(root,observed)
    year = target_year(calendar,observed) if year is None else year
    admission = None
    if str(year) in calendar.ranges:
        marker = f'{REGISTRY}/{year}.json'
        admission = (dict(read(root/marker),registrySha256=sha(root/marker)) if marker in calendar.files
                     else dict(admittedAt=None,calendarSha256=calendar.digest))
    checks, issues = scheduled(root,store,year,observed)
    newest = max(checks,key=lambda item:instant(item['archiveVerifiedAt']),default=None)
    return dict(schemaVersion=1,year=year,asOf=observed.isoformat(),
                admissionState='admitted' if admission is not None else 'awaiting_exchange_evidence',
                admission=admission,verifiedScheduledChecks=len(checks),scheduledIssues=issues,
                latestScheduled=newest,latestManual=manual(project,year,observed))
