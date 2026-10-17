#!/usr/bin/env python3
"""Synchronize standalone source into the canonical HTML reading copy."""
import argparse
from html import escape, unescape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def synchronize(write=False):
    count = 0
    for program in json.loads((ROOT / 'code/programs.json').read_text())['programs']:
        page = ROOT / program['page']
        text = page.read_text()
        for language, path in program['files'].items():
            pattern = r'(<code id="code-' + language + r'" data-source="' + re.escape(path) + r'">)(.*?)(</code>)'
            matches = list(re.finditer(pattern, text, re.S))
            if len(matches) != 1:
                raise ValueError(f'Expected one reading copy: {path}')
            expected = (ROOT / path).read_text()
            if write:
                text = re.sub(pattern, lambda m: m[1] + escape(expected) + m[3], text, flags=re.S)
            elif unescape(matches[0][2]) != expected:
                raise ValueError(f'Stale reading copy: {path}')
            count += 1
        if write:
            page.write_text(text)
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps({'synchronized_sources': synchronize(args.write)}))
