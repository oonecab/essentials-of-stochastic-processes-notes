#!/usr/bin/env python3
"""Copy a finished build into the deploy queue, then atomically mark ready."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import re
from durability import sync_directory, sync_tree

def queue_release(source, queue, builder_root):
    source = Path(source).resolve(strict=True)
    release_id = source.name
    if not re.fullmatch(r'\d{8}T\d{6}', release_id) or source.parent != Path(builder_root).resolve(strict=True):
        raise ValueError('Unexpected build result')
    target = queue/release_id
    if target.exists() or target.is_symlink():
        raise ValueError('Queue entry exists')
    stage = Path(tempfile.mkdtemp(prefix='.incoming-', dir=queue))
    subprocess.run(['rsync','-rlt','--',str(source)+'/',str(stage)+'/'],check=True)
    for p in stage.rglob('*'):
        p.chmod(0o775 if p.is_dir() else 0o664)
    stage.chmod(0o775)
    sync_tree(stage)
    os.rename(stage,target)
    sync_directory(queue)
    return {'queued':release_id}


if __name__ == '__main__':
    row=json.loads(Path(sys.argv[1]).read_text())
    if Path(row['directory']).name != row['release_id']:
        raise ValueError('Build identity differs')
    print(json.dumps(queue_release(Path(row['directory']), Path('/var/spool/reading-notes/ready'),
                                   Path('/opt/reading-notes-builder/deploy/portal-releases'))))
