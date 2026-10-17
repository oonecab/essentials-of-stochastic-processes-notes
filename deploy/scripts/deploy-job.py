#!/usr/bin/env python3
"""Publish queued immutable packages; keep processed receipts outside the web root."""
import json
from pathlib import Path
import re
import subprocess

queue=Path('/var/spool/reading-notes/ready')
done=Path('/var/spool/reading-notes/done')
for package in sorted(queue.iterdir()):
    if not re.fullmatch(r'\d{8}T\d{6}',package.name): continue
    if package.is_symlink(): raise ValueError('Queue symlink rejected')
    subprocess.run(['/usr/local/lib/reading-notes/deploy/scripts/publish.sh','--release-dir',str(package)],check=True)
    package.rename(done/package.name)
    print(json.dumps({'published':package.name}))
