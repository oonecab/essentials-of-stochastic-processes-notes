#!/usr/bin/env python3
"""Synchronize registered code blocks, preserving HTML attributes and source bytes."""
from collections import Counter
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
CONTROLLED = ROOT.parents[1] / 'src/content/books/measure-probability'


def check_displayed(displayed, expected):
    if unescape(displayed) != expected:
        raise ValueError('displayed code differs from maintained source')


class CodeBlocks(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text, self.blocks, self.active = text, [], None
        self.lines = [0]
        for index, char in enumerate(text):
            if char == '\n':
                self.lines.append(index + 1)
        self.feed(text)
        self.close()
        if self.active is not None:
            raise ValueError('unclosed displayed source block')

    def source_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if self.active is not None:
            raise ValueError('unescaped markup inside displayed source')
        sources = [value for name, value in attrs if name == 'data-source']
        if sources:
            if tag != 'code' or len(sources) != 1 or not sources[0]:
                raise ValueError('invalid displayed source boundary')
            self.active = (sources[0], self.source_offset() + len(self.get_starttag_text()))

    def handle_endtag(self, tag):
        if self.active is not None:
            if tag != 'code':
                raise ValueError('unexpected closing tag inside displayed source')
            source, start = self.active
            self.blocks.append((source, start, self.source_offset()))
            self.active = None

    def handle_comment(self, data):
        if self.active is not None:
            raise ValueError('unescaped comment inside displayed source')


def replace_blocks(text, expected, write=False):
    blocks = CodeBlocks(text).blocks
    actual = Counter(source for source, _, _ in blocks)
    if actual != Counter({source: 1 for source in expected}):
        raise ValueError('displayed sources differ from programs.json')
    for source, start, end in reversed(blocks):
        if not write:
            check_displayed(text[start:end], expected[source])
        else:
            text = text[:start] + escape(expected[source]) + text[end:]
    return text


def synchronize(write=False):
    registered = json.loads((ROOT / 'code/programs.json').read_text())['programs']
    pages, sources = {}, set()
    for program in registered:
        page = Path(program['page'])
        if page.parent != Path('notes') or page.suffix != '.html':
            raise ValueError('invalid registered reading page')
        for name in program['files'].values():
            source = (ROOT / name).resolve()
            if source.parent != ROOT / 'code' or source.suffix not in ('.py', '.c') or name in sources:
                raise ValueError('invalid or duplicate registered source: ' + name)
            sources.add(name)
            pages.setdefault(page.name, {})[name] = source.read_text()
    # Controlled HTML is authoritative; the retained compatibility copy is checked
    # and regenerated in the same operation, without changing either tag's attrs.
    for directory in (CONTROLLED, ROOT / 'notes'):
        if not directory.is_dir():
            raise ValueError('missing reading source directory: ' + str(directory))
        found = set()
        for page in sorted(directory.glob('*.html')):
            expected = pages.get(page.name, {})
            text = page.read_text()
            updated = replace_blocks(text, expected, write)
            if expected:
                found.add(page.name)
            if write and updated != text:
                page.write_text(updated)
        if found != set(pages):
            raise ValueError('registered code page missing')
    return len(sources)


def parser_regressions():
    expected = {'code/test.py': 'print("<code> & value")\n'}
    html = '<pre><code class="python" data-source=\'code/test.py\' title="literal">' + escape(expected['code/test.py']) + '</code></pre>'
    assert replace_blocks(html, expected) == html
    replaced = replace_blocks(html, {'code/test.py': '# changed\n'}, True)
    assert 'class="python"' in replaced and 'title="literal"' in replaced and '# changed\n' in replaced
    rejected = []
    for name, bad in [('nested_tag', html.replace('&lt;code&gt;', '<code>')),
                      ('missing_end', html.replace('</code>', '')),
                      ('duplicate_source', html + html),
                      ('wrong_source', html.replace('code/test.py', '../test.py'))]:
        try:
            replace_blocks(bad, expected)
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError('source parser accepted mutation: ' + name)
    return rejected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps({'synchronized_sources': synchronize(args.write), 'parser_mutations_rejected': parser_regressions()}))
