#!/usr/bin/env python3
"""Import one reviewed book without retyping or serializing its HTML."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'books/stochastic/tools'))
from html_support import Document


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--book', required=True)
    args = ap.parse_args()
    state_file = ROOT / 'scripts/migration-state.json'
    state = json.loads(state_file.read_text())
    books = {b['id']: b for b in json.loads((ROOT/'books/catalog.json').read_text())['books']}
    book = books[args.book]
    order = ['measure-probability', 'visual-group-theory', 'stochastic', 'weiss', 'csapp']
    if args.book in state['migrated_books']:
        raise ValueError('Book already imported; controlled sources are now the maintenance entry')
    if state['migrated_books'] != order[:order.index(args.book)]:
        raise ValueError('Migration must follow the registered book order')
    for previous in state['migrated_books']:
        gate = ROOT / f'tmp/reading-notes-migration/gates/{previous}.json'
        if not gate.exists() or json.loads(gate.read_text())['status'] != 'Go':
            raise ValueError('Previous book has not passed its gate: '+previous)
    manifest_path = ROOT/book['directory']/'notes/source_manifest.json'
    if not manifest_path.exists():
        manifest_path = ROOT/book['directory']/'source_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    target = ROOT/'src/content/books'/args.book
    target.mkdir(parents=True, exist_ok=False)
    imported = []
    for source in sorted((ROOT/book['directory']/'notes').glob('*.html')):
        raw = source.read_bytes()
        original = subprocess.check_output(['git','show',state['baseline_ref']+':'+source.relative_to(ROOT).as_posix()],cwd=ROOT)
        if raw != original:
            raise ValueError('Source differs from the frozen starting commit: '+source.name)
        text = raw.decode(); document = Document(text); nodes = list(document.root.walk())
        title = next(n.text() for n in nodes if n.tag == 'title')
        match = re.match(r'chapter(\d+)',source.name)
        chapter = int(match[1]) if match else 'appendix_a' if source.name.startswith('appendix') else source.stem
        candidates = manifest.get('chapters', [])+manifest.get('front_matter', [])
        item = next((x for x in candidates if x.get('file') == source.name or x.get('chapter') == chapter or x.get('name') == ('chapter'+match[1] if match else chapter)), {})
        pages = {k:item.get(k) for k in ['printed_start','printed_end','pdf_start','pdf_end']}
        for prefix in ['printed','pdf']:
            if prefix+'_pages' in item:
                pages[prefix+'_start'],pages[prefix+'_end']=item[prefix+'_pages'][0],item[prefix+'_pages'][-1]
        if source.stem == 'preface':
            special = {'measure-probability':['I','IV',6,9], 'visual-group-theory':['ix',2,10,17], 'csapp':[19,34,20,35]}.get(args.book)
            if special:pages=dict(zip(pages,special))
        header = next((n.text() for n in nodes if n.tag=='header'),'')
        if match and pages['pdf_start'] is None:
            printed = re.search(r'印刷(?:页码?|页)?\s*(\d+)\s*[—–-]\s*(\d+)',header)
            pdf = re.search(r'PDF\s*(?:第\s*)?(?:页(?:序|码)?\s*)?(\d+)\s*[—–-]\s*(\d+)',header)
            if printed:pages['printed_start'],pages['printed_end']=map(int,printed.groups())
            if pdf:pages['pdf_start'],pages['pdf_end']=map(int,pdf.groups())
        if args.book == 'weiss' and match:
            # Original chapter headers establish the +17 mapping; chapter 3 only
            # states printed pages. Include all exercise source-page attributes.
            assert pages['printed_start'] is not None, source.name
            if pages['pdf_start'] is not None:
                assert pages['pdf_start'] - pages['printed_start'] == 17, source.name
            exercise_pages = [int(p) for n in nodes
                              for p in re.findall(r'\d+', n.attrs.get('data-source-pdf-pages', ''))]
            pages['pdf_start'] = pages['printed_start'] + 17
            pages['pdf_end'] = max(pages['printed_end'] + 17, *exercise_pages)
            pages['printed_end'] = pages['pdf_end'] - 17
        if match and any(value is None for value in pages.values()):
            raise ValueError('Unresolved chapter source range: ' + source.name)
        exercises=[n.attrs.get('data-exercise',n.attrs.get('id')) for n in nodes if n.has_class('exercise') and n.attrs.get('id','').startswith('ex')]
        metadata={'book':args.book,'chapter':chapter,'title':title,**pages,
                  'exercise_range':[exercises[0],exercises[-1]] if exercises else [],
                  'statement_count':sum(n.has_class('statement') or n.has_class('source-statement') for n in nodes),
                  'source_manifest':manifest_path.relative_to(ROOT).as_posix(),
                  'route':book['publish_prefix']+'/notes/'+source.name,
                  'legacy_path':source.relative_to(ROOT).as_posix(),
                  'original_sha256':hashlib.sha256(raw).hexdigest(),
                  'source_scope_note':'章节范围按来源清单；总览跨全书，空范围表示不适用；序言的分段位置以原 HTML 来源说明为准。'}
        if args.book == 'weiss':
            metadata['source_scope_note'] = '按原 HTML 章首正文页和全部习题 data-source-pdf-pages 合并范围；各章页映射为印刷页加 17，参考文献范围另见原章首。总览跨全书，空范围表示不适用。'
        def extract(m):
            kind='styles' if m[1]=='style' else 'scripts'
            extension='css' if kind=='styles' else 'js'
            name=f"{kind}/{hashlib.sha256(m[3].encode()).hexdigest()[:20]}.{extension}"
            dest=ROOT/'src'/name;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and dest.read_text()!=m[3]:raise ValueError('Shared asset collision')
            dest.write_text(m[3])
            return '<'+m[1]+m[2]+'>\x3c!-- RN:include '+name+' --></'+m[1]+'>'
        content=re.sub(r'<(style|script)([^>]*)>([\s\S]*?)</\1>',extract,text)
        (target/source.name).write_text('---\n'+json.dumps(metadata,ensure_ascii=False,indent=2)+'\n---\n'+content)
        imported.append(metadata)
    if len(imported)!=book['expected_pages']:raise ValueError('Missing pages')
    state['migrated_books'].append(args.book)
    state_file.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'book':args.book,'pages':len(imported),'source_bytes':sum((ROOT/x['legacy_path']).stat().st_size for x in imported)},ensure_ascii=False))


if __name__ == '__main__':main()
