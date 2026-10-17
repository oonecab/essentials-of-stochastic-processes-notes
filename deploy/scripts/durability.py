"""POSIX durability barriers shared by the installer and queue writer."""
import json
import os
from pathlib import Path
import stat
import tempfile


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def sync_file(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('Only regular files may enter a durable release')
        os.fsync(fd)
    finally:
        os.close(fd)


def sync_tree(root):
    """Flush payload and metadata, then directory entries from leaves to root."""
    root = Path(root)
    directories = [root]
    for path in sorted(root.rglob('*')):
        kind = path.lstat().st_mode
        if stat.S_ISREG(kind):
            sync_file(path)
        elif stat.S_ISDIR(kind):
            directories.append(path)
        else:
            raise ValueError('Non-regular release entry: '+str(path))
    for path in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        sync_directory(path)


def atomic_json(path, value, checkpoint=lambda phase: None):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=path.name+'.tmp-', dir=path.parent)
    pending = Path(name)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        checkpoint('journal-temp')
        os.replace(pending, path)
        sync_directory(path.parent)
    finally:
        pending.unlink(missing_ok=True)


def durable_unlink(path):
    path = Path(path)
    path.unlink(missing_ok=True)
    sync_directory(path.parent)
