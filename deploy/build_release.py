#!/usr/bin/env python3
"""Build a checked static release containing notes, downloadable code and the PDF."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import gzip
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import unquote, urljoin, urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from html_support import check_resources
INDEX = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0;url=notes/book_overview.html"><title>Durrett 随机过程读书笔记</title></head>
<body><p><a href="notes/book_overview.html">进入全书地图</a></p></body></html>
'''.encode('utf-8')


def write_archive(path, blobs):
    """Fixed gzip and tar metadata; equal site bytes produce an equal archive."""
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as tar:
                for name, blob in sorted(blobs.items()):
                    info = tarfile.TarInfo(name)
                    info.size, info.mode, info.uid, info.gid, info.mtime = len(blob), 0o644, 0, 0, 0
                    tar.addfile(info, io.BytesIO(blob))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-id', default=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%dT%H%M%S'))
    parser.add_argument('--web-root', default='/var/www/essentials-of-stochastic-processes/current',
                        help='Path used by the generated Nginx server include')
    args = parser.parse_args()
    if not re.fullmatch(r'\d{8}T\d{6}', args.release_id):
        parser.error('release ID must be YYYYMMDDTHHMMSS')
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', args.web_root) or '..' in args.web_root.split('/'):
        parser.error('web root must be an absolute Nginx-safe path')
    parent = ROOT / 'deploy/releases'
    parent.mkdir(parents=True, exist_ok=True)
    out = parent / args.release_id
    if out.exists():
        parser.error(f'Release already exists: {out}')
    checked = subprocess.run([sys.executable, ROOT / 'tools/check_notes.py', '--extract-only'],
                             check=True, capture_output=True, text=True)
    validation = json.loads(checked.stdout)['extracted']
    code_manifest = json.loads((ROOT / 'code/programs.json').read_text())
    source_manifest = json.loads((ROOT / 'notes/source_manifest.json').read_text())
    paths = sorted((ROOT / 'notes').glob('*.html')) + sorted((ROOT / 'notes').glob('*.json'))
    paths += [ROOT / 'code/README.md', ROOT / 'code/Makefile', ROOT / 'code/programs.json']
    for program in code_manifest['programs']:
        paths += [ROOT / p for p in program['files'].values()]
        paths.append((ROOT / program['files']['c']).parent / 'README.md')
    paths.append(ROOT / source_manifest['web_pdf']['path'])
    sources = {p.relative_to(ROOT).as_posix(): p for p in paths}
    blobs = {name: p.read_bytes() for name, p in sources.items()}
    blobs['index.html'] = INDEX
    scripts = set()
    for name, blob in blobs.items():
        if name.endswith('.json') and (b'/Users/' in blob or b'file:///' in blob):
            raise ValueError(f'Machine-local path in public metadata: {name}')
        if not name.endswith('.html'):
            continue
        scan = check_resources(blob.decode('utf-8'), name, packaged=blobs, allow_entry_refresh=True)
        scripts.update(scan['scripts'])
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js is required to check the inline navigation scripts')
    with tempfile.TemporaryDirectory(prefix='notes-js-check-') as temporary:
        for i, script in enumerate(sorted(scripts)):
            path = Path(temporary) / f'inline-{i}.js'
            path.write_text(script)
            subprocess.run([node, '--check', path], check=True, capture_output=True, text=True)
    for name, path in sources.items():
        if path.read_bytes() != blobs[name]:
            raise RuntimeError(f'Source changed during packaging: {name}')
    script_hashes = ["'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'"
                     for s in sorted(scripts)]
    records = [{'path': name, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}
               for name, blob in sorted(blobs.items())]
    config = (ROOT / 'deploy/nginx-static.inc.template').read_text()
    config = config.replace('@@WEB_ROOT@@', args.web_root).replace('@@SCRIPT_SOURCES@@', ' '.join(script_hashes))
    with tempfile.TemporaryDirectory(prefix='.release-', dir=parent) as staging:
        staging = Path(staging)
        archive = staging / 'site.tar.gz'
        write_archive(archive, blobs)
        metadata = {
            'release_id': args.release_id,
            'created_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
            'entry_point': 'index.html', 'reading_entry': 'notes/book_overview.html',
            'files': records, 'total_bytes': sum(r['bytes'] for r in records),
            'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'web_pdf': source_manifest['web_pdf'],
            'inline_script_csp_sources': script_hashes, 'validation': validation,
            'inline_script_syntax_check': 'pass',
            'archive_reproducibility': 'gzip mtime=0, empty filename; USTAR entries sorted, mtime/uid/gid=0',
        }
        (staging / 'release.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
        (staging / 'SHA256SUMS').write_text(''.join(f"{r['sha256']}  {r['path']}\n" for r in records))
        (staging / 'archive.sha256').write_text(metadata['archive_sha256'] + '  site.tar.gz\n')
        (staging / 'nginx-static.inc').write_text(config)
        staging.rename(out)
    print(json.dumps({'release_id': args.release_id, 'directory': str(out),
                      'files': len(records), 'bytes': metadata['total_bytes'],
                      'html_pages': validation['html_pages'], 'source_files': validation['standalone_source_files'],
                      'pdf_included': True, 'link_validation': 'pass',
                      'inline_script_syntax_check': 'pass'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
