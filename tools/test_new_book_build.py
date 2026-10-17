#!/usr/bin/env python3
"""Build an added two-page book in an isolated local clone, including CSP and packaging."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parent = ROOT / 'tmp/new-book-build'
    parent.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='run-', dir=parent))
    checkout = run / 'checkout'
    log = run / 'commands.log'

    def command(args, cwd=checkout):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
        with log.open('a') as output:
            output.write(json.dumps(args) + '\n' + result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'New-book fixture failed; see {log}')
        return result.stdout

    command(['git', 'clone', '--shared', '--no-hardlinks', str(ROOT), str(checkout)], cwd=ROOT)
    # Exercise the actual working source, including uncommitted repair files;
    # git history in the clone still provides the immutable I028 baseline.
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode().split('\0')
    for name in filter(None, names):
        source, target = ROOT / name, checkout / name
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif target.exists():
            target.unlink()
    (checkout / 'node_modules').symlink_to(ROOT / 'node_modules', target_is_directory=True)
    session = ROOT / 'tmp/final-assessment/browser-session.json'
    if session.exists():
        target = checkout / session.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(session, target)
    policy = json.loads((checkout / 'deploy/publish-allowlist.json').read_text())
    for name in policy['authorized_pdfs']:
        source = ROOT / 'books' / name
        target = checkout / 'books' / name
        if source.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    book = checkout / 'books/dummy'
    for folder in ('notes', 'code', 'tools'):
        (book / folder).mkdir(parents=True)
    (book / 'agent.md').write_text('Isolated build fixture only.\n')
    checker = '''import json\nfrom pathlib import Path\nr=Path(__file__).resolve().parents[1]\npages=sorted((r/'notes').glob('*.html'))\nassert len(pages)==2\nassert sum(p.read_text().count('id="ex-1-1"') for p in pages)==1\nprint(json.dumps({'status':'passed','pages':len(pages)}))\n'''
    (book / 'tools/check_notes.py').write_text(checker)
    save(book / 'notes/source_manifest.json', {'fixture': True, 'pages': ['book_overview.html', 'chapter01_fixture.html']})
    routes = []
    for filename, title, exercise in [('book_overview.html', 'Dummy overview', ''),
                                       ('chapter01_fixture.html', 'Dummy chapter', '<details class="exercise" id="ex-1-1"><summary>Exercise 1</summary><p>Fixture answer.</p></details>')]:
        nav = '<p class="chapter-nav"><a href="book_overview.html">Overview</a><a href="chapter01_fixture.html#content">Chapter</a></p>'
        raw = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<title>{title}</title><style>body{{margin:0}} main{{max-width:60em;margin:5em auto;padding:1em}}</style></head><body>'
               f'<main id="top"><header><h1>{title}</h1>{nav}</header><section id="content"><h2>Content</h2><p>Added catalog fixture.</p>{exercise}</section>'
               f'<footer>{nav}</footer></main><script>const wide=matchMedia("(min-width:1100px)");document.documentElement.style.scrollPaddingTop=(wide.matches ? 100 : 110)+"px";</script></body></html>')
        (book / 'notes' / filename).write_text(raw)
        route = 'dummy/notes/' + filename
        routes.append(route)
        metadata = {'book': 'dummy', 'chapter': filename, 'title': title, 'printed_start': None, 'printed_end': None,
                    'pdf_start': None, 'pdf_end': None, 'exercise_range': [], 'statement_count': 0,
                    'source_manifest': 'books/dummy/notes/source_manifest.json', 'route': route,
                    'legacy_path': 'books/' + route, 'original_sha256': hashlib.sha256(raw.encode()).hexdigest()}
        target = checkout / 'src/content/books/dummy' / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('---\n' + json.dumps(metadata) + '\n---\n' + raw)
    command(['git', 'add', 'books/dummy', 'src/content/books/dummy'])
    command(['git', '-c', 'user.name=Reading Notes Fixture', '-c', 'user.email=fixture@example.invalid',
             '-c', 'commit.gpgsign=false', 'commit', '-m', 'test fixture: freeze dummy sources'])
    baseline = command(['git', 'rev-parse', 'HEAD']).strip()
    catalog_path = checkout / 'books/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    expected_reading = sum(b['expected_pages'] for b in catalog['books']) + len(routes)
    catalog['books'].append({'id': 'dummy', 'title': 'Dummy book', 'directory': 'books/dummy',
                            'entry': 'notes/book_overview.html', 'publish_prefix': 'dummy', 'notes_directory': 'notes',
                            'code_directory': 'code', 'guidelines': 'agent.md', 'expected_pages': len(routes),
                            'expected_exercises': 1, 'code_authority': 'standalone_sources', 'checker': 'tools/check_notes.py'})
    save(catalog_path, catalog)
    state_path = checkout / 'scripts/migration-state.json'
    state = json.loads(state_path.read_text())
    state['migrated_books'].append('dummy')
    state.setdefault('book_baselines', {})['dummy'] = baseline
    save(state_path, state)
    for route in [*routes, 'dummy/index.html', 'dummy/notes/source_manifest.json']:
        policy['files'].append({'path': route, 'mode': 'public-summary' if route.endswith('.json') else 'copy'})
    save(checkout / 'deploy/publish-allowlist.json', policy)
    for file in (book / 'notes').glob('*.html'):
        file.unlink()  # Build must generate absent compatibility mirrors itself.
    release_id = '20990101T000001'
    command(['pnpm', 'build', '--release-id', release_id])
    command([sys.executable, str(book / 'tools/check_notes.py'), '--quick'])
    release = checkout / 'deploy/portal-releases' / release_id
    meta = json.loads((release / 'release.json').read_text())
    parity = json.loads((checkout / 'tmp/reading-notes-migration/parity/all.json').read_text())
    assert meta['reading_pages'] == expected_reading == parity['pages']
    assert all(not row['differences'] for row in parity['records'])
    assert all((book / 'notes' / Path(route).name).is_file() for route in routes)
    assert 'dummy' in (release / 'nginx-static.inc').read_text() and '@@' not in (release / 'nginx-static.inc').read_text()
    assert 'dummy/notes/book_overview.html' in (checkout / 'dist/index.html').read_text()
    # Exact publisher inventory independently reads the generated package tree.
    command([sys.executable, 'deploy/public_policy.py', 'dist'])
    report = {'status': 'passed', 'checkout': str(checkout.relative_to(ROOT)), 'added_pages': len(routes),
              'reading_pages': meta['reading_pages'], 'public_html': meta['html_pages'], 'files': len(meta['files']),
              'parity_differences': 0, 'generated_mirrors': len(routes), 'nginx_book_route': 'dummy',
              'csp_browser': json.loads((checkout / 'tmp/reading-notes-migration/csp/report.json').read_text())['status'],
              'release_archive_sha256': meta['archive_sha256'], 'scope': 'isolated full build/package; no production action'}
    save(run / 'report.json', report)
    print(json.dumps({**report, 'report': str((run / 'report.json').relative_to(ROOT))}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
