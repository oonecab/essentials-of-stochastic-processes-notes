#!/usr/bin/env python3
"""Build Astro, validate the exact public inventory and package an immutable release."""
import argparse
import base64
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urljoin, urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_portal import Resources, Document, BOOKS, write_archive
from public_policy import inspect, sums, POLICY


def package(release_id):
    parent = ROOT / 'deploy/portal-releases'
    parent.mkdir(parents=True, exist_ok=True)
    out = parent / release_id
    if out.exists():
        raise ValueError('Release already exists: ' + release_id)
    rows = inspect(ROOT / 'dist')
    blobs = {r['path']: (ROOT / 'dist' / r['path']).read_bytes() for r in rows}
    scans, scripts, navigation = {}, set(), []
    for name, blob in blobs.items():
        if name.endswith('.html'):
            scan = Resources()
            scan.feed(blob.decode())
            scan.close()
            Document(blob.decode())
            scans[name] = scan
            scripts.update(scan.scripts)
    refs = 0
    for name, scan in scans.items():
        for tag, key, ref in scan.references:
            u = urlsplit(ref)
            if u.scheme in {'file', 'javascript', 'vbscript'}:
                raise ValueError('Nonportable resource: ' + ref)
            if u.scheme or u.netloc:
                if tag != 'a' and u.scheme != 'data':
                    raise ValueError('External dependency: ' + ref)
                continue
            target = unquote(urlsplit(urljoin('https://notes.zzzping.top/' + name, ref)).path).lstrip('/')
            if not target or target.endswith('/'):
                target += 'index.html'
            if target not in blobs or (u.fragment and target in scans and unquote(u.fragment) not in scans[target].ids):
                raise ValueError(f'Broken link in {name}: {ref}')
            refs += 1
        for item in scan.links:
            u = urlsplit(urljoin('https://notes.zzzping.top/' + name, item['href']))
            navigation.append({'source': name, **item, 'target': u.path.lstrip('/'),
                               'fragment': unquote(u.fragment), 'external': u.netloc != 'notes.zzzping.top'})
    hashes = ["'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'" for s in sorted(scripts)]
    with tempfile.TemporaryDirectory(prefix='.astro-release-', dir=parent) as temp:
        stage = Path(temp)
        for i, script in enumerate(sorted(scripts)):
            p = stage / 'inline.js'
            p.write_text(script)
            subprocess.run(['node', '--check', p], check=True, capture_output=True)
        p.unlink(missing_ok=True)
        write_archive(stage / 'site.tar.gz', blobs)
        metadata = {'schema_version': 2, 'builder': 'Astro static 7.4.0', 'release_id': release_id,
            'domain': 'notes.zzzping.top',
            'source_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'source_tree_dirty': bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
            'toolchain': {'node':'24.21.0','pnpm':'11.21.0','astro':'7.4.0'}, 'files': rows, 'total_bytes': sum(r['bytes'] for r in rows),
            'html_pages': len(scans), 'reading_pages': 54, 'local_references_checked': refs,
            'archive_sha256': hashlib.sha256((stage/'site.tar.gz').read_bytes()).hexdigest(),
            'inline_script_csp_sources': hashes, 'inline_script_syntax_check': 'pass',
            'entry_redirects': {f'/{b}{s}': f'/{b}/notes/book_overview.html' for b in BOOKS for s in ('','/','/index.html')},
            'navigation': {b: f'{b}/notes/book_overview.html' for b in BOOKS},
            'navigation_inventory_file': 'navigation.json', 'navigation_links': len(navigation),
            'publish_policy_sha256': hashlib.sha256(POLICY.read_bytes()).hexdigest(),
            'build_report': 'tmp/reading-notes-migration/build.json',
            'scope': 'Static release; original Python checks remain independent. Production not deployed.'}
        (stage / 'release.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
        (stage / 'navigation.json').write_text(json.dumps(navigation, ensure_ascii=False, indent=2)+'\n')
        (stage / 'SHA256SUMS').write_text(sums(rows))
        (stage / 'archive.sha256').write_text(metadata['archive_sha256']+'  site.tar.gz\n')
        (stage / 'nginx-static.inc').write_text((ROOT/'deploy/nginx/static.inc.template').read_text().replace('@@SCRIPT_SOURCES@@',' '.join(hashes)))
        (stage / 'nginx-notes.zzzping.top.conf').write_bytes((ROOT/'deploy/nginx/notes.conf.template').read_bytes())
        stage.rename(out)
    return {'release_id': release_id, 'directory': str(out), 'files': len(rows),
            'html_pages': len(scans), 'reading_pages':54, 'bytes': metadata['total_bytes']}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--release-id', default=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%dT%H%M%S'))
    ap.add_argument('--package-dist', action='store_true', help=argparse.SUPPRESS)
    a = ap.parse_args()
    if not re.fullmatch(r'\d{8}T\d{6}', a.release_id):
        ap.error('Release ID must be YYYYMMDDTHHMMSS')
    if (ROOT/'deploy/portal-releases'/a.release_id).exists():
        ap.error('Release already exists')
    if a.package_dist:
        owner = json.loads((ROOT/'tmp/reading-notes-migration/build.lock/owner.json').read_text())
        if owner['pid'] != os.getppid():
            raise ValueError('Packaging requires the active parent build lock')
        print(json.dumps(package(a.release_id),ensure_ascii=False))
        sys.exit(0)
    log = ROOT / 'tmp/reading-notes-migration/package-build.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w') as output:
        result = subprocess.run(['pnpm', 'build', '--release-id', a.release_id], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        sys.exit('Astro build failed; see ' + str(log.relative_to(ROOT)))
    directory=ROOT/'deploy/portal-releases'/a.release_id
    meta=json.loads((directory/'release.json').read_text())
    print(json.dumps({'release_id':a.release_id,'directory':str(directory),
                      'files':len(meta['files']),'reading_pages':meta['reading_pages'],
                      'bytes':meta['total_bytes']},ensure_ascii=False,indent=2))
