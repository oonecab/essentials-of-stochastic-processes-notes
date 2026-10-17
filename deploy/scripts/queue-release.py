#!/usr/bin/env python3
"""Copy a finished build into the deploy queue, then atomically mark ready."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

row=json.loads(Path(sys.argv[1]).read_text())
source=Path(row['directory']).resolve(strict=True)
queue=Path('/var/spool/reading-notes/ready')
release_id=row['release_id']
if not source.is_relative_to(Path('/opt/reading-notes-builder/deploy/portal-releases')) or source.name!=release_id:
    raise ValueError('Unexpected build result')
target=queue/release_id
if target.exists(): raise ValueError('Queue entry exists')
stage=Path(tempfile.mkdtemp(prefix='.incoming-',dir=queue))
subprocess.run(['rsync','-rlt','--',str(source)+'/',str(stage)+'/'],check=True)
for p in stage.rglob('*'): p.chmod(0o775 if p.is_dir() else 0o664)
stage.chmod(0o775)
os.rename(stage,target)
print(json.dumps({'queued':release_id}))
