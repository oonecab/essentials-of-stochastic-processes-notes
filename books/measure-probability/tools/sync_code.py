#!/usr/bin/env python3
"""Keep displayed code identical to the maintained standalone sources."""
from html import escape, unescape
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]


def check_displayed(displayed, expected):
    if unescape(displayed) != expected:
        raise ValueError('displayed code differs from maintained source')


def synchronize(write=False):
    count = 0
    for page in sorted((ROOT / 'notes').glob('*.html')):
        text = page.read_text()
        def replace(match):
            nonlocal count
            source = (ROOT / match[1]).resolve()
            if ROOT / 'code' not in source.parents or source.suffix not in ('.py', '.c'):
                raise ValueError('invalid code source: ' + match[1])
            expected = source.read_text()
            count += 1
            if not write:
                check_displayed(match[2], expected)
            return f'<code data-source="{match[1]}">{escape(expected)}</code>'
        updated = re.sub(r'<code data-source="([^"]+)">(.*?)</code>', replace, text, flags=re.S)
        if write and updated != text:
            page.write_text(updated)
    if count != 6:
        raise ValueError('expected three C11/Python source pairs')
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(synchronize(args.write))
