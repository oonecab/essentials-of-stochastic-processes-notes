#!/usr/bin/env python3
"""Publish queued immutable packages; keep processed receipts outside the web root."""
import json
from pathlib import Path
import re
import subprocess
import os
from publish_release import verified
from durability import sync_directory


def process_queue(root, queue, done, publisher):
    for package in sorted(queue.iterdir()):
        if not re.fullmatch(r'\d{8}T\d{6}', package.name):
            continue
        if package.is_symlink():
            raise ValueError('Queue symlink rejected')
        target = 'releases/' + package.name
        # Recover a service interruption between successful publish and receipt.
        already = (not (root/'.publish-transaction.json').exists()
                   and (root/'current').is_symlink()
                   and os.readlink(root/'current') == target)
        if already:
            installed = verified(root/target)
            if installed != json.loads((package/'release.json').read_text()):
                raise ValueError('Queued release identity differs from installed current')
        else:
            subprocess.run([str(publisher), '--release-dir', str(package)], check=True)
        package.rename(done/package.name)
        sync_directory(done)
        sync_directory(queue)
        print(json.dumps({'published':package.name, 'recovered_receipt':already}))


if __name__ == '__main__':
    process_queue(Path('/srv/reading-notes'), Path('/var/spool/reading-notes/ready'),
                  Path('/var/spool/reading-notes/done'),
                  Path('/usr/local/lib/reading-notes/deploy/scripts/publish.sh'))
