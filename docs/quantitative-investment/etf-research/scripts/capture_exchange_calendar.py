"""Capture, verify or register an annual mainland exchange calendar."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from etf_research.exchange_calendar import REGISTRY, SOURCES, calendar_at, inspect_annual, official_url, verify_annual
from etf_research.http_capture import fetch, load_policy, save_transport
from etf_research.policy_events import instant
from etf_research.publication import create, seal, sha, sync_dir


def now():
    return datetime.now(timezone.utc)


def capture(folder,year,urls):
    for name,url in urls.items():
        if not url or not official_url(name,url):
            raise ValueError('Supply the exact HTTPS annual announcement URL for '+name)
    policy = load_policy()
    folder.mkdir(parents=True,exist_ok=False)
    save_transport(folder,policy)
    rows = []
    for name,url in urls.items():
        rows.append(dict(fetch(folder,name,url,policy,additional_hosts=tuple(SOURCES.values())),
                         receivedAt=now().isoformat()))
    create(folder/'requests.json',rows)
    try:
        result = inspect_annual(folder,year,now().isoformat())
        create(folder/'calendar.json',result)
    except (OSError,KeyError,TypeError,ValueError) as error:
        create(folder/'failure.json',dict(year=year,observedAt=now().isoformat(),error=str(error)))
        raise
    finally:
        seal(folder)
    return verify_annual(folder)


def register(folder,root):
    folder,root = folder.resolve(),root.resolve()
    if folder.parent!=root/'data/snapshots':
        raise ValueError('Annual source must be an immutable data/snapshots bundle')
    value = verify_annual(folder)
    available = now()
    year = value['year']
    if (year!=max(map(int,calendar_at(root,available).ranges))+1
            or instant(value['checkedAt'])>available):
        raise ValueError('Annual calendar is out of sequence or not yet verified')
    record = dict(schemaVersion=1,year=year,snapshot=folder.relative_to(root).as_posix(),
                  manifestSha256=sha(folder/'manifest.json'),admittedAt=available.isoformat())
    registry = root/REGISTRY
    registry.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.pending-',dir=registry) as pending:
        proposed = Path(pending)/'record'
        create(proposed,record)
        os.link(proposed,registry/(str(year)+'.json'))
    sync_dir(registry)
    calendar_at(root,available)
    return record


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--year',type=int)
    modes.add_argument('--verify',type=Path)
    modes.add_argument('--register',type=Path)
    parser.add_argument('--sse')
    parser.add_argument('--szse')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if args.year is not None:
        if not 2000<=args.year<=2100 or args.output is None:
            parser.error('Capture needs --year 2000–2100 and --output')
        result = capture(args.output,args.year,dict(sse=args.sse,szse=args.szse))
    elif args.verify:
        result = verify_annual(args.verify)
    else:
        result = register(args.register,ROOT)
    print(json.dumps(result,ensure_ascii=False))
