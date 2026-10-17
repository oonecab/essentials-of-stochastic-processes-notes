#!/usr/bin/env python3
"""Bind a completed, actually inspected book migration to its retained evidence."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'tmp/reading-notes-migration'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book', required=True)
    parser.add_argument('--python-report', required=True)
    parser.add_argument('--visual-note', required=True,
                        help='Actual human/agent image review observations, never inferred from screenshots existing')
    args = parser.parse_args()
    book = ROOT / 'books' / args.book
    review = book / 'review'
    parity_path = STAGE / 'parity' / (args.book + '.json')
    browser_path = STAGE / 'browser' / args.book / 'report.json'
    python_path = ROOT / args.python_report
    parity = json.loads(parity_path.read_text())
    browser = json.loads(browser_path.read_text())
    python = json.loads(python_path.read_text())
    assert parity['status'] == browser['status'] == 'passed'
    assert all(not r['differences'] and r['js_ratio'] <= 1.5 for r in parity['records'])
    assert not browser['external_requests'] and not browser['errors']
    assert len(browser['views']) == 4 * parity['pages']
    assert len(browser['no_js']) == parity['pages']
    assert python['status'] == 'passed' and not python['quick'], python.keys()
    assert python['book'] in [args.book, 'all']
    for r in parity['records']:
        assert digest(ROOT / 'dist' / r['page']) == r['output_sha256']
    for shot in browser['screenshots']:
        assert digest(ROOT / shot['file']) == shot['sha256']
    now = datetime.now(timezone.utc).isoformat()
    evidence = {p.relative_to(ROOT).as_posix(): digest(p)
                for p in [parity_path, browser_path, python_path]}
    record = {
        'schema_version': 1, 'book': args.book, 'recorded_at_utc': now, 'status': 'Go',
        'scope': 'Astro 静态迁移；原正文、数学、代码和历史内容审阅保持。',
        'baseline_ref': parity['baseline_ref'], 'pages': parity['pages'],
        'counts': {key: sum(r['source_counts'][key] for r in parity['records'])
                   for key in parity['records'][0]['source_counts']},
        'source_bytes': sum(r['source_bytes'] for r in parity['records']),
        'output_bytes': sum(r['output_bytes'] for r in parity['records']),
        'js_bytes': sum(r['js_bytes'] for r in parity['records']),
        'max_js_ratio': max(r['js_ratio'] for r in parity['records']),
        'parity_differences': [], 'external_requests': [],
        'script_additions': {r['page']: r['script_additions'] for r in parity['records'] if r.get('script_additions')},
        'js_views': len(browser['views']), 'no_js_views': len(browser['no_js']),
        'visual_review': args.visual_note,
        'evidence_sha256': evidence, 'screenshots': browser['screenshots'],
        'open_findings': [],
        'boundaries': ['实体手机和真实读屏器未验证', '本次只做本地迁移；生产未部署',
                       '原数学与程序审阅的历史范围不因迁移验收而扩大'],
    }
    save(review / 'astro-migration.json', record)
    save(review / 'content-baseline-astro.json', {
        'schema_version': 1, 'kind': 'additive_migration_baseline',
        'baseline_ref': parity['baseline_ref'], 'records': parity['records'],
        'note': '原内容完整性基线保持；此文件追加原源文件与 Astro 输出的身份及逐页 parity。',
    })
    save(review / 'release-astro.json', {
        'schema_version': 1, 'scope': 'local_dist_reading_pages',
        'files': {r['page']: r['output_sha256'] for r in parity['records']},
    })
    # Existing review schemas and historical evidence are preserved verbatim except
    # explicit current documentation bindings. Content changes are never rebaselined here.
    validation_path = review / 'validation.json'
    validation = json.loads(validation_path.read_text()) if validation_path.exists() else {
        'schema_version': 1, 'book': args.book, 'status': 'migration_verified',
        'historical_review_entry': 'notes/validation.json' if (book/'notes/validation.json').exists()
                                   else 'notes/README.md',
        'file_sha256': {}, 'open_findings': [],
    }
    updates = []
    for name, old in validation.get('file_sha256', {}).items():
        new = digest(book / name)
        if new != old:
            assert name in ['agent.md', 'notes/README.md'], 'Unexpected changed reviewed file: ' + name
            updates.append({'file': name, 'previous_sha256': old, 'current_sha256': new,
                            'reason': 'Astro 迁移后维护路径说明；正文和计算规则保持'})
            validation['file_sha256'][name] = new
    for name in ['agent.md', 'notes/README.md']:
        validation['file_sha256'][name] = digest(book/name)
    if updates:
        validation.setdefault('migration_binding_history', []).append({'at': now, 'updates': updates})
    validation['astro_migration'] = {'record': 'review/astro-migration.json',
        'sha256': digest(review/'astro-migration.json'), 'status': 'Go', 'open_findings': [],
        'source_sha256': {r['page'].split('/notes/')[1]: r['source_sha256'] for r in parity['records']}}
    validation.setdefault('open_findings', [])
    save(validation_path, validation)
    browser_target = review / 'browser.json'
    browser_record = json.loads(browser_target.read_text()) if browser_target.exists() else {'schema_version': 1}
    browser_record['astro_migration'] = {'status': 'passed', 'record': 'review/astro-migration.json',
        'sha256': digest(review/'astro-migration.json'), 'widths': [1800, 1440, 1024, 390],
        'js_views': len(browser['views']), 'no_js_views': len(browser['no_js']),
        'external_requests': [], 'visual_review': args.visual_note}
    save(browser_target, browser_record)
    save(STAGE/'gates'/(args.book+'.json'), record)
    print(json.dumps({key: record[key] for key in ['book', 'status', 'pages', 'counts', 'output_bytes', 'js_bytes']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
