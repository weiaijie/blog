"""Incremental content-addressed archives; restore only into a new directory.

An archive captures evidence, not proof that an interrupted run is publishable.
No extraction of tar paths, symlinks, credentials or live destination overwrite.
"""
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import hashlib, os, re, shutil, tempfile
from .publication import read, encoded, create, lock, sha, sync_dir, atomic

DYNAMIC = ('data/snapshots', 'reports/daily', 'reports/operations', 'reports/health',
           'reports/notice-reviews', 'reports/notice-decisions')
POINTERS = ('config/active_run.json', 'site/operation_status.json', 'site/health_status.json')
EXTENSIONS = {'.json', '.body', '.py', '.txt', '.md', '.csv', '.html', '.css', '.js', '.log', '.pdf', '.png', '.svg', '.headers'}

def safe_path(root, name):
    p = PurePosixPath(name)
    if not isinstance(name, str) or '\\' in name or ':' in name or p.is_absolute() or not p.parts or any(x in ('.', '..') for x in p.parts) or str(p) != name:
        raise ValueError('Unsafe archive path')
    root = Path(root).resolve(); target = root.joinpath(*p.parts)
    for part in [target, *target.parents]:
        if part == root: break
        if part.is_symlink(): raise ValueError('Archive symlinks are forbidden')
    if not target.resolve().is_relative_to(root): raise ValueError('Archive path escapes root')
    return target

def inventory(root):
    root = Path(root); names = set(read(root / 'config/archive_inventory.json')['files'])
    for prefix in DYNAMIC:
        folder = safe_path(root, prefix)
        if not folder.exists(): continue
        for p in folder.rglob('*'):
            if p.is_symlink(): raise ValueError('Runtime evidence contains symlink')
            if not p.is_file(): continue
            rel = p.relative_to(root).as_posix()
            if '__pycache__' in p.parts or p.suffix == '.pyc': continue
            if any(x.startswith('.') for x in p.relative_to(folder).parts):
                raise ValueError('Unreviewed runtime file type: ' + rel)
            if p.suffix not in EXTENSIONS:
                # Only previously reviewed, sealed market inputs may use these opaque formats.
                manifest = p.parent / 'manifest.json'
                if (prefix != 'data/snapshots' or p.suffix not in {'.zip', '.jsonl'} or
                        rel not in names or not safe_path(root, manifest.relative_to(root).as_posix()).is_file() or
                        read(manifest).get(p.name) != sha(p)):
                    raise ValueError('Unreviewed runtime file type: ' + rel)
            names.add(rel)
    names.update(p for p in POINTERS if (root / p).exists())
    for name in names:
        if any(x in ('.env', '.git', '.ssh', '.runtime', '__pycache__') or x.startswith('.env.') for x in PurePosixPath(name).parts): raise ValueError('Private/cache path excluded')
        if not safe_path(root, name).is_file(): raise ValueError('Missing inventory file: ' + name)
    return sorted(names)

def object_path(store, value):
    if not re.fullmatch('[a-f0-9]{64}', value): raise ValueError('Invalid content digest')
    return safe_path(store, 'objects/' + value[:2] + '/' + value)

def capture(root, store, names=None):
    root, store = Path(root).resolve(), Path(store).resolve()
    if store.is_relative_to(root) or root.is_relative_to(store): raise ValueError('Archive store must be separate from project')
    store.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        stack.enter_context(lock(store / 'archive.lock'))
        for name in ('scheduler', 'daily', 'review', 'health'):
            stack.enter_context(lock(root / '.runtime' / (name + '.lock')))
        automatic_inventory = names is None
        names = sorted(names if names is not None else inventory(root))
        entries = {}; new_objects = 0; new_bytes = 0
        for name in names:
            p = safe_path(root, name); body = p.read_bytes(); value = hashlib.sha256(body).hexdigest()
            obj = object_path(store, value); obj.parent.mkdir(parents=True, exist_ok=True)
            if obj.exists():
                if sha(obj) != value: raise ValueError('Existing archive object is corrupt')
            else:
                if shutil.disk_usage(store).free < len(body) + 100 * 1024 * 1024: raise ValueError('Insufficient archive free space')
                fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=obj.parent)
                try:
                    with os.fdopen(fd,'wb') as f: f.write(body); f.flush(); os.fsync(f.fileno())
                    # Publish only complete objects; link fails if the hash already exists.
                    os.link(temporary,obj)
                finally:
                    os.unlink(temporary)
                sync_dir(obj.parent); new_objects += 1; new_bytes += len(body)
            entries[name] = dict(sha256=value, bytes=len(body))
        # Guard concurrent/manual writers that do not participate in the locks.
        if any(sha(safe_path(root, name)) != e['sha256'] for name,e in entries.items()): raise ValueError('Source changed during archive')
        if automatic_inventory and names != inventory(root): raise ValueError('Inventory changed')
        snapshot = dict(schema_version=1, created_at_utc=datetime.now(timezone.utc).isoformat(), files=entries,
                        new_objects=new_objects, new_bytes=new_bytes, restores_only_to_new_directory=True)
        identity = hashlib.sha256(encoded(snapshot)).hexdigest()
        path = safe_path(store, 'snapshots/' + identity + '.json'); create(path, snapshot); sync_dir(path.parent)
        result=dict(snapshot=identity, files=len(entries), new_objects=new_objects, new_bytes=new_bytes)
        atomic(root/'.runtime/archive_status.json',dict(result,finished_at_utc=datetime.now(timezone.utc).isoformat()))
        return result

def verify(store, identity):
    if not re.fullmatch('[a-f0-9]{64}', identity): raise ValueError('Invalid snapshot identity')
    path = safe_path(store, 'snapshots/' + identity + '.json')
    if sha(path) != identity: raise ValueError('Archive manifest changed')
    snapshot = read(path)
    if snapshot.get('schema_version') != 1 or not snapshot.get('files'): raise ValueError('Invalid archive format')
    for name,e in snapshot['files'].items():
        safe_path(Path(store) / 'validation-root', name)
        obj = object_path(store, e['sha256'])
        if obj.stat().st_size != e['bytes'] or sha(obj) != e['sha256']: raise ValueError('Archive content mismatch: ' + name)
    return snapshot

def restore(store, identity, destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink(): raise ValueError('Restore destination must not exist')
    if destination.resolve().is_relative_to(Path(store).resolve()): raise ValueError('Cannot restore inside archive store')
    snapshot = verify(store, identity)  # Verify every object before writing anything.
    destination.mkdir(parents=True, exist_ok=False)
    for name,e in snapshot['files'].items():
        target = safe_path(destination, name); target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f: f.write(object_path(store, e['sha256']).read_bytes()); f.flush(); os.fsync(f.fileno())
        if sha(target) != e['sha256']: raise ValueError('Restore verification failed')
    sync_dir(destination)
    return dict(snapshot=identity, verified_files=len(snapshot['files']), destination_was_new=True, activates_services=False)

def compare(store, identity, destination):
    snapshot = verify(store, identity); added=[]; conflicts=[]; same=0
    for name,e in snapshot['files'].items():
        p = safe_path(destination, name)
        if not p.exists(): added.append(name)
        elif sha(p) != e['sha256']: conflicts.append(name)
        else: same += 1
    return dict(added=added, conflicts=conflicts, identical=same, writes_performed=0)
