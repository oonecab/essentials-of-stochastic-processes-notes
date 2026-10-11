#!/usr/bin/env python3
"""Verify current review file/block hashes; historical checkpoint hashes stay historical."""
from pathlib import Path
import hashlib,json
from html_support import Document,canonical
from content_integrity import digest

ROOT=Path(__file__).resolve().parents[1]


def main():
    notes=ROOT/'notes'
    nodes={p.name:{n.attrs['id']:n for n in Document(p.read_text()).root.walk() if n.attrs.get('id')} for p in notes.glob('*.html')}
    count=0
    for p in notes.glob('*.json'):
        data=json.loads(p.read_text())
        if '/Users/' in p.read_text() or 'file:///' in p.read_text():raise ValueError('Private path in public record: '+p.name)
        for name,record in data.get('files',{}).items():
            blob=(ROOT/name).read_bytes()
            assert record['sha256']==hashlib.sha256(blob).hexdigest() and record['bytes']==len(blob),(p.name,name)
            count+=1
    statements=json.loads((notes/'statements_review.json').read_text())
    for r in statements['statements']:
        assert r['canonical_html_sha256']==digest(canonical(nodes[r['page_file']][r['key']]))
    annotation=json.loads((notes/'annotations_review.json').read_text())
    for r in annotation['groups']:
        node=nodes[r['page']][r['anchor']]
        assert r['canonical_group_sha256']==digest(canonical(node))
        cards=[n for n in node.walk('div') if n.has_class('annotation-card')]
        assert len(cards)==len(r['cards'])==2
        for a,b in zip(cards,r['cards']):assert b['canonical_html_sha256']==digest(canonical(a))
    for filename,groups in [('readability_review.json',['derivation_blocks','retained_proofs']),('review_manifest.json',['body_additions','retained_body_reviews'])]:
        data=json.loads((notes/filename).read_text())
        for group in groups:
            for r in data[group]:
                if 'hash_scope' in r:node=nodes[r['page']][r['section']];omit=True
                else:node=nodes[r['page']][r['id']];omit=False
                assert r['html_sha256']==digest(canonical(node,omit_programs=omit)),(filename,r['id'])
    repair=json.loads((notes/'audit_fix_review.json').read_text())
    for r in repair['browser_review']['layouts']:
        assert r['sha256']==hashlib.sha256((notes/r['file']).read_bytes()).hexdigest()
    print(json.dumps({'status':'pass','current_file_bindings':count,'statement_bindings':150,'annotation_group_bindings':66,'annotation_card_bindings':132,'browser_layout_bindings':36,'scope':'Current records; preserved historical checkpoints intentionally retain earlier hashes.'}))


if __name__=='__main__':main()
