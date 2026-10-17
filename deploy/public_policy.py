"""Exact public inventory, used by both build and publisher (standard library only)."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

POLICY = Path(__file__).with_name('publish-allowlist.json')


def safe_name(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or p.as_posix() != name or '..' in p.parts
            or '\\' in name or any(c in name for c in '\r\n\0')
            or any(x.startswith('.') or x in {'content', 'review', 'tmp', 'src', 'node_modules'} for x in p.parts)
            or 'baseline' in p.name.lower() or p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}):
        raise ValueError('Non-public path: ' + name)
    return name


def load_policy():
    data = json.loads(POLICY.read_text())
    rows = data['files']
    names = [safe_name(r['path']) for r in rows]
    if len(names) != len(set(names)) or any(r['mode'] not in {'copy', 'public-summary'} for r in rows):
        raise ValueError('Invalid allowlist')
    if {n for n in names if n.endswith('.pdf')} != set(data['authorized_pdfs']):
        raise ValueError('Unregistered PDF')
    return data


def summary(name):
    # Fixed public text, never copy arbitrary review fields into the web root.
    return (json.dumps({'schema_version': 1, 'kind': 'public_record_summary',
        'book': name.split('/')[0], 'record': PurePosixPath(name).stem,
        'scope': '本地址保留资料引用入口。完整审阅、数值夹具与来源核对记录由仓库维护；阅读正文及页码链接见本书笔记。'},
        ensure_ascii=False, indent=2) + '\n').encode()


def inspect(site, transform=False):
    site = Path(site)
    if site.is_symlink() or not site.is_dir():
        raise ValueError('Site must be a real directory')
    actual = {}
    for p in site.rglob('*'):
        name = p.relative_to(site).as_posix()
        if p.is_symlink() or not (p.is_dir() or p.is_file()):
            raise ValueError('Non-regular public entry: ' + name)
        safe_name(name)
        if p.is_file():
            actual[name] = p
    policy = load_policy()
    expected = {r['path']: r for r in policy['files']}
    if actual.keys() != expected.keys():
        raise ValueError(f'Allowlist mismatch: extra={sorted(actual.keys()-expected.keys())}, missing={sorted(expected.keys()-actual.keys())}')
    for name, row in expected.items():
        p = actual[name]
        if row['mode'] == 'public-summary':
            if transform:
                p.write_bytes(summary(name))
            if p.read_bytes() != summary(name):
                raise ValueError('Raw private evidence at public summary URL: ' + name)
        if p.suffix == '.pdf' and hashlib.sha256(p.read_bytes()).hexdigest() != policy['authorized_pdf_sha256'][name]:
            raise ValueError('Registered PDF bytes changed: ' + name)
        if p.suffix == '.json' and (b'/Users/' in p.read_bytes() or b'file:///' in p.read_bytes()):
            raise ValueError('Local path in public JSON: ' + name)
        if p.suffix == '.zip':
            with zipfile.ZipFile(p) as archive:
                for item in archive.infolist():
                    safe_name(item.filename.rstrip('/'))
                    if item.external_attr >> 16 & 0o170000 == 0o120000:
                        raise ValueError('Symlink in download archive')
    if transform:
        for name in ['stochastic/notes/review_manifest.html', 'stochastic/notes/validation.html']:
            p = site / name
            p.write_text(p.read_text().replace('下载原始记录', '下载公开摘要'))
    return [{'path': n, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for n, p in sorted(actual.items())]


def sums(rows):
    return ''.join(f"{r['sha256']}  {r['path']}\n" for r in rows)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('site', type=Path)
    ap.add_argument('--transform', action='store_true')
    ap.add_argument('--sums', type=Path)
    a = ap.parse_args()
    rows = inspect(a.site, a.transform)
    if a.sums:
        a.sums.write_text(sums(rows))
    print(json.dumps({'status': 'passed', 'files': len(rows), 'bytes': sum(r['bytes'] for r in rows)}))
