"""Immutable run bundles and a single atomic active pointer (Ubuntu runtime)."""
from contextlib import contextmanager
from pathlib import Path
import hashlib,json,os,tempfile

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def inside(root,name):
    p=(Path(root)/name).resolve()
    if not p.is_relative_to(Path(root).resolve()):raise ValueError('Path escapes project')
    return p
def create(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(encoded(value));f.flush();os.fsync(f.fileno())
def sync_dir(path):
    fd=os.open(path,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.pointer-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(encoded(value));f.flush();os.fsync(f.fileno())
        os.replace(tmp,path);sync_dir(path.parent)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
@contextmanager
def lock(path):
    import fcntl
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    # Keep the inode; unlinking a flock file allows competing locks on new inodes.
    with path.open('a+b') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)
def seal(folder):
    folder=Path(folder)
    files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
    if 'manifest.json' in files:raise ValueError('Bundle already sealed')
    for name in files:
        with (folder/name).open('rb') as f:os.fsync(f.fileno())
    for p in sorted((p for p in folder.rglob('*') if p.is_dir()),reverse=True):sync_dir(p)
    create(folder/'manifest.json',files);sync_dir(folder)
def verify_bundle(folder):
    folder=Path(folder);manifest=read(folder/'manifest.json')
    actual={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
    if set(manifest)!=actual:raise ValueError('Bundle file set changed')
    for name,value in manifest.items():
        if sha(inside(folder,name))!=value:raise ValueError('Bundle hash mismatch: '+name)
def promote(root,folder,pointer,hook=lambda stage:None):
    """Caller holds lock. Recovery repeats this; no published file is rewritten."""
    root=Path(root);folder=inside(root,folder);pointer=inside(root,pointer)
    verify_bundle(folder);ready=read(folder/'ready.json');new=ready['pointer']
    new={**new,'bundle_manifest_sha256':sha(folder/'manifest.json')}
    current=read(pointer)
    if current==new:return 'already_published'
    if sha(pointer)!=ready['previous_pointer_sha256']:raise ValueError('Active pointer changed; refuse stale publication')
    for name,value in ready['input_sha256'].items():
        if sha(inside(root,name))!=value:raise ValueError('Input changed since preparation: '+name)
    if new['as_of']<current['as_of']:raise ValueError('Cannot roll back active day')
    if new['as_of']==current['as_of'] and new['checkpoint_sha256']!=current['checkpoint_sha256']:raise ValueError('Cannot revise published account')
    checkpoint=read(inside(root,new['checkpoint']))
    from .forward import digest,engine_digest
    if checkpoint['checkpoint_sha256']!=digest({k:v for k,v in checkpoint.items() if k!='checkpoint_sha256'}) or checkpoint['engine_sha256']!=engine_digest():raise ValueError('Invalid prepared checkpoint')
    if checkpoint['checkpoint_sha256']!=new['checkpoint_sha256'] or checkpoint['as_of']!=new['as_of']:raise ValueError('Pointer/checkpoint mismatch')
    hook('before_pointer');atomic(pointer,new);hook('after_pointer')
    return 'published'
