#!/usr/bin/env python3
"""Locked, validated immutable release installation and atomic current switch."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid

DEPLOY = Path(__file__).resolve().parents[1]
ROOT = DEPLOY.parent
sys.path[:0] = [str(DEPLOY), str(ROOT/'tools')]
from public_policy import inspect, sums, POLICY
from release_support import extract_release
from durability import atomic_json, durable_unlink, sync_directory, sync_tree


def identity(value):
    if not re.fullmatch(r'\d{8}T\d{6}', value):
        raise ValueError('Release ID must be YYYYMMDDTHHMMSS')
    return value


def verified(directory):
    if directory.is_symlink():
        raise ValueError('Release must be a real directory')
    for name in ['release.json', 'SHA256SUMS']:
        if (directory/name).is_symlink() or not (directory/name).is_file():
            raise ValueError('Non-regular release metadata')
    meta = json.loads((directory/'release.json').read_text())
    identity(meta['release_id'])
    if meta.get('publish_policy_sha256') != hashlib.sha256(POLICY.read_bytes()).hexdigest():
        raise ValueError('Release allowlist version is not installed')
    rows = inspect(directory/'site')
    if rows != meta['files'] or (directory/'SHA256SUMS').read_text() != sums(rows):
        raise ValueError('Release inventory or SHA256SUMS differs')
    # GNU sha256sum on Ubuntu; macOS has shasum. Both validate the supplied list.
    sha = shutil.which('sha256sum')
    command = [sha, '-c', str(directory/'SHA256SUMS')] if sha else ['shasum', '-a', '256', '-c', str(directory/'SHA256SUMS')]
    subprocess.run(command, cwd=directory/'site', check=True, stdout=subprocess.DEVNULL)
    return meta


def atomic_link(root, target):
    pending = root / ('.current-' + uuid.uuid4().hex)
    try:
        os.symlink(target, pending)
        os.replace(pending, root/'current')
        sync_directory(root)
    finally:
        pending.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path('/srv/reading-notes'))
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--release-dir', type=Path)
    mode.add_argument('--rollback', type=identity)
    mode.add_argument('--recover', action='store_true')
    ap.add_argument('--restore-release', type=identity, help='With --recover, explicitly select a verified release when the journal is damaged')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--service-hook', type=Path, help='Only for local dry-run; executable called with test/reload')
    ap.add_argument('--lock-fd', type=int, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.restore_release and not a.recover:
        ap.error('--restore-release requires --recover')
    root = a.root.resolve(strict=True)
    if a.root.is_symlink() or not root.is_dir() or root == Path('/'):
        raise ValueError('Unsafe root')
    if a.dry_run and not (root.is_relative_to(ROOT/'tmp') or root.is_relative_to(Path(tempfile.gettempdir()).resolve())):
        raise ValueError('Dry-run requires a temporary directory')
    if not a.dry_run and (root != Path('/srv/reading-notes') or a.service_hook):
        raise ValueError('Production uses the fixed root and installed root-owned service helper')
    if a.service_hook:
        a.service_hook = a.service_hook.resolve(strict=True)
    lock_fd = a.lock_fd if a.lock_fd is not None else os.open(root/'.publish.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        print('Another publish holds the lock', file=sys.stderr)
        return 75
    releases = root/'releases'
    if releases.is_symlink():
        raise ValueError('Untrusted releases symlink')
    releases.mkdir(exist_ok=True)
    sync_directory(root)
    current = root/'current'
    if current.exists() and not current.is_symlink():
        raise ValueError('current must be a managed symlink')
    previous = os.readlink(current) if current.is_symlink() else None
    previous_meta = None
    if previous:
        if not re.fullmatch(r'releases/\d{8}T\d{6}', previous) or ((not a.recover and not a.rollback) and not (root/previous).is_dir()):
            raise ValueError('Untrusted or broken current')
        if not a.rollback and not a.recover:
            previous_meta = verified(root/previous)
    journal = root/'.publish-transaction.json'

    def checkpoint(phase):
        # Actual SIGKILL injection is confined to isolated dry-runs.
        if a.dry_run and os.environ.get('READING_NOTES_TEST_CRASH') == phase:
            os.kill(os.getpid(), signal.SIGKILL)

    def service(action):
        if a.service_hook:
            subprocess.run([str(a.service_hook), action], check=True)
        elif not a.dry_run:
            subprocess.run(['sudo', '-n', '/usr/local/sbin/reading-notes-nginx', action], check=True)

    if a.recover:
        if not journal.exists():
            if previous:
                verified(root/previous)
            print(json.dumps({'status':'no-pending-transaction','current':previous}))
            return 0
        if journal.is_symlink() or not journal.is_file():
            raise ValueError('Journal must be a regular file')
        damaged = False
        try:
            data = json.loads(journal.read_text())
            if not isinstance(data, dict) or set(data) != {'previous','candidate'}:
                raise ValueError('Invalid journal fields')
            for key, value in data.items():
                if not (key == 'previous' and value is None) and not (isinstance(value, str) and re.fullmatch(r'releases/\d{8}T\d{6}', value)):
                    raise ValueError('Invalid journal target')
        except (ValueError, UnicodeError) as error:
            damaged = True
            if not a.restore_release:
                print(json.dumps({'status':'journal-damaged','changed':False,'error':str(error),
                    'recovery':'Inspect releases and run --recover --restore-release YYYYMMDDTHHMMSS; the selected payload is verified before switching and the damaged journal is retained outside the web root.'}), file=sys.stderr)
                return 2
        target = 'releases/'+a.restore_release if a.restore_release else data['previous']
        if target:
            if not re.fullmatch(r'releases/\d{8}T\d{6}', target):
                raise ValueError('Bad recovery target')
            verified(root/target)
            atomic_link(root,target)
        else:
            durable_unlink(current)
        if target:
            service('test'); service('reload')
        if damaged:
            os.replace(journal, root/('.publish-transaction.corrupt-'+uuid.uuid4().hex+'.json'))
            sync_directory(root)
        else:
            durable_unlink(journal)
        print(json.dumps({'status':'recovered','current':target}))
        return 0
    if journal.exists():
        raise ValueError('Interrupted transaction: run --recover before publishing')
    if a.rollback:
        candidate = releases/a.rollback
        meta = verified(candidate)
        if meta['release_id'] != a.rollback:
            raise ValueError('Rollback directory identity differs')
    else:
        source = a.release_dir.resolve(strict=True)
        for n in ['release.json','SHA256SUMS','site.tar.gz']:
            if (source/n).is_symlink() or not (source/n).is_file():
                raise ValueError('Release package must contain regular files')
        release_id = identity(json.loads((source/'release.json').read_text())['release_id'])
        candidate = releases/release_id
        if candidate.exists() or candidate.is_symlink():
            raise ValueError('Immutable release already exists: '+release_id)
        with tempfile.TemporaryDirectory(prefix='.unpack-', dir=root) as temp:
            unpack = Path(temp)
            meta = extract_release(source, unpack/'site')
            checkpoint('unpack')
            for name in ['release.json','SHA256SUMS']:
                shutil.copyfile(source/name,unpack/name)
            verified(unpack)
            for value in meta['inline_script_csp_sources']:
                if not re.fullmatch(r"'sha256-[A-Za-z0-9+/]{43}='", value):
                    raise ValueError('Invalid CSP source')
            (unpack/'nginx-static.inc').write_text((DEPLOY/'nginx/static.inc.template').read_text().replace('@@SCRIPT_SOURCES@@',' '.join(meta['inline_script_csp_sources'])))
            incoming = releases/('.incoming-'+uuid.uuid4().hex)
            incoming.mkdir()
            try:
                subprocess.run(['rsync','-rlt','--',str(unpack)+'/',str(incoming)+'/'],check=True)
                checkpoint('rsync')
                verified(incoming)
                for p in incoming.rglob('*'):
                    p.chmod(0o555 if p.is_dir() else 0o444)
                sync_tree(incoming)
                incoming.rename(candidate)
                candidate.chmod(0o555)
                sync_directory(candidate)
                sync_directory(releases)
                checkpoint('rename')
            except BaseException:
                # Keep any partially copied candidate out of current; operator may inspect it.
                raise
    if not a.dry_run:
        installed = Path('/etc/nginx/snippets/reading-notes-static.inc').read_text()
        required_sources = set(meta['inline_script_csp_sources']) | set((previous_meta or {}).get('inline_script_csp_sources', []))
        if not all(s in installed for s in required_sources):
            raise ValueError('New scripts require an administrator-reviewed CSP snippet update')
    target = 'releases/'+meta['release_id']
    atomic_json(journal, {'previous':previous,'candidate':target}, checkpoint)
    checkpoint('journal')
    switched = False
    def interrupted(signum, frame):
        raise RuntimeError('Publish interrupted by signal '+str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        switched = True
        atomic_link(root,target)
        checkpoint('switch')
        service('test')
        service('reload')
    except BaseException as error:
        if switched:
            if previous:
                atomic_link(root,previous)
            else:
                durable_unlink(current)
        rollback_error = None
        if previous:
            try:
                service('test'); service('reload')
            except BaseException as failure:
                rollback_error = str(failure)
        if not rollback_error:
            durable_unlink(journal)
        print(json.dumps({'status':'failed','restored_current':previous,
                          'error':str(error),'rollback_service_error':rollback_error}), file=sys.stderr)
        return 1
    durable_unlink(journal)
    print(json.dumps({'status':'passed','mode':'dry-run' if a.dry_run else 'publish',
                      'release_id':meta['release_id'],'current':target,'previous':previous,
                      'service_validation':'hook' if a.service_hook else ('skipped' if a.dry_run else 'nginx/systemd')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
