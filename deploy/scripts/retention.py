"""Space guard and conservative release retention, called while holding publish flock."""
import json
import os
from pathlib import Path
import re
import shutil
import time
from durability import sync_directory

ID = re.compile(r'\d{8}T\d{6}')


def capacity(root, payload_bytes=0, files=0, min_free_bytes=512*1024*1024, min_free_inodes=10000):
    fs=os.statvfs(root)
    available=fs.f_bavail*fs.f_frsize
    # Unpack, candidate and private package snapshot coexist during installation.
    required=3*payload_bytes+min_free_bytes
    inodes=3*files+min_free_inodes
    result={'available_bytes':available,'available_inodes':fs.f_favail,
            'required_bytes':required,'required_inodes':inodes}
    if available < required or fs.f_favail < inodes:
        raise ValueError('Insufficient publication headroom: '+json.dumps(result))
    return result


def remove_tree(path):
    """Only real, same-device trees; never follow links or cross mounts."""
    if path.is_symlink() or not path.is_dir() or path.is_mount():
        raise ValueError('Unsafe cleanup directory')
    device=path.stat().st_dev
    for child in path.rglob('*'):
        if child.is_symlink() or child.lstat().st_dev != device or child.is_mount():
            raise ValueError('Unexpected cleanup entry: '+str(child))
    # Root can remove read-only releases; isolated macOS tests need writable dirs.
    for child in [path,*path.rglob('*')]:
        if child.is_dir(): child.chmod(0o700)
    shutil.rmtree(path)
    sync_directory(path.parent)


def stale_temporaries(root, age_seconds=86400, now=None):
    if (root/'.publish-transaction.json').exists(): return []
    now=time.time() if now is None else now
    patterns=[(root,re.compile(r'\.(?:unpack|package)-[a-zA-Z0-9_-]+'),False),
              (root/'releases',re.compile(r'\.incoming-[a-f0-9]{32}'),False),
              (root,re.compile(r'\.current-[a-f0-9]{32}'),True)]
    removed=[]
    for parent,pattern,link in patterns:
        for item in parent.iterdir():
            if not pattern.fullmatch(item.name) or now-item.lstat().st_mtime < age_seconds:continue
            if link:
                if not item.is_symlink():raise ValueError('Unexpected pending link type')
                item.unlink();sync_directory(parent)
            else:remove_tree(item)
            removed.append(str(item.relative_to(root)))
    return removed


def retention_plan(root, keep_last_n=3, min_age_days=7, now=None):
    if keep_last_n < 2:raise ValueError('Retain at least two releases')
    now=time.time() if now is None else now
    protected=set()
    if (root/'current').is_symlink():protected.add(os.readlink(root/'current'))
    for filename in ['.publish-transaction.json','.last-publish.json']:
        p=root/filename
        if p.exists():
            if p.is_symlink():raise ValueError('Unsafe retention journal')
            data=json.loads(p.read_text())
            protected.update(v for k,v in data.items() if k in {'previous','candidate','current'} and isinstance(v,str))
    versions=sorted((p for p in (root/'releases').iterdir() if ID.fullmatch(p.name)),key=lambda p:p.name,reverse=True)
    protected.update('releases/'+p.name for p in versions[:keep_last_n])
    return [p for p in versions if 'releases/'+p.name not in protected and now-p.lstat().st_mtime>=min_age_days*86400]
