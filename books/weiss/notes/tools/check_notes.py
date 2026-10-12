#!/usr/bin/env python3
"""Check the book's HTML and build programs from its canonical code blocks.

Only the Python standard library is needed. Run --help for the output options.
Generated files go to the requested directory, never back into the notes.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import itertools
import io
import json
import math
import platform
from pathlib import Path
import re
import random
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

NOTES = Path(__file__).resolve().parents[1]
EXERCISES = [5, 25, 26, 46, 36, 44, 15, 14, 41, 60, 14, 36]
VOID = set("area base br col embed hr img input link meta param source track wbr".split())


@dataclass
class Node:
    tag: str
    attrs: dict[str, str]
    line: int
    parent: Node | None = None
    parts: list = field(default_factory=list)

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()

    def text(self):
        return "".join(p.text() if isinstance(p, Node) else p for p in self.parts)

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.nodes, self.stack = path, [], []
        self.feed(path.read_text(encoding="utf-8"))
        self.ids = {n.attrs["id"]: n for n in self.nodes if "id" in n.attrs}
        self.codes = {
            n.attrs["id"]: n for n in self.nodes
            if n.tag == "code" and n.attrs.get("data-language") in ("c", "python")
            and any(a.has_class("code-pair") for a in n.ancestors())
        }

    def handle_starttag(self, tag, attrs):
        n = Node(tag, dict(attrs), self.getpos()[0], self.stack[-1] if self.stack else None)
        if n.parent:
            n.parent.parts.append(n)
        self.nodes.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, value):
        if self.stack:
            self.stack[-1].parts.append(value)


def check(pages):
    errors, rows, styles, scripts = [], [], set(), set()
    by_file = {p.path.name: p for p in pages}
    for p in pages:
        fail = lambda message: errors.append(f"{p.path.name}: {message}")
        ids = Counter(n.attrs["id"] for n in p.nodes if "id" in n.attrs)
        for id, count in ids.items():
            if count != 1:
                fail(f"duplicate ID {id}")
        styles.add(next(n.text() for n in p.nodes if n.tag == "style"))
        scripts.add(next(n.text() for n in p.nodes if n.tag == "script"))
        sidebars = [n for n in p.nodes if n.has_class("chapter-sidebar")]
        navs = [n for n in p.nodes if n.tag == "nav"]
        if len(sidebars) != 1 or len(navs) != 1 or not any(a is sidebars[0] for a in navs[0].ancestors()):
            fail("expected exactly one sidebar table of contents")
        for n in p.nodes:
            for attribute in ("href", "src"):
                raw = n.attrs.get(attribute)
                if not raw:
                    continue
                u = urlsplit(raw)
                if u.scheme or u.netloc:
                    continue
                target = (p.path.parent / unquote(u.path)).resolve() if u.path else p.path
                if not target.exists():
                    fail(f"missing local target {raw}")
                elif target.suffix == ".html" and u.fragment:
                    other = by_file.get(target.name)
                    if other is None or unquote(u.fragment) not in other.ids:
                        fail(f"missing anchor {raw}")
        pairs = [n for n in p.nodes if n.has_class("code-pair")]
        for pair in pairs:
            versions = [n for n in pair.parts if isinstance(n, Node) and n.has_class("code-version")]
            if [n.attrs.get("data-language") for n in versions] != ["c", "python"]:
                fail(f"unpaired languages at {pair.attrs.get('id')}")
            elif "open" not in versions[0].attrs:
                fail(f"C code collapsed by default at {pair.attrs.get('id')}")
        exercises = [n for n in p.nodes if n.has_class("exercise")]
        match = re.match(r"chapter(\d+)_", p.path.name)
        if match:
            chapter = int(match[1])
            wanted = [f"ex{chapter}-{i}" for i in range(1, EXERCISES[chapter - 1] + 1)]
            if [n.attrs.get("id") for n in exercises] != wanted:
                fail("exercise numbers are incomplete or out of order")
            for i, ex in enumerate(exercises, 1):
                children = [n for n in ex.parts if isinstance(n, Node)]
                questions = [n for n in children if n.has_class("exercise-question")]
                answers = [n for n in children if n.has_class("answer")]
                if len(questions) != 1 or len(answers) != 1 or children.index(questions[0]) > children.index(answers[0]):
                    fail(f"question/answer order at {ex.attrs.get('id')}")
                    continue
                q = questions[0]
                if q.attrs.get("data-original-exercise") != f"{chapter}.{i}":
                    fail(f"original problem number at {ex.attrs.get('id')}")
                nums = re.findall(r"\d+", q.attrs.get("data-source-pdf-pages", ""))
                if not nums or any(not 1 <= int(v) <= 518 for v in nums):
                    fail(f"PDF source pages at {ex.attrs.get('id')}")
            ex_links = [n for n in p.nodes if n.tag == "a" and n.attrs.get("href") == "#exercises"
                        and any(a.tag == "nav" for a in n.ancestors())]
            title = f"习题解答 · {chapter}.1–{chapter}.{EXERCISES[chapter - 1]}"
            if len(ex_links) != 1 or ex_links[0].text().strip() != title:
                fail("table of contents exercise range differs from the chapter")
        rows.append({"file": p.path.name, "exercises": len(exercises), "pairs": len(pairs)})
    if len(styles) != 1 or len(scripts) != 1:
        errors.append("pages must share exactly one CSS and navigation script")
    return {"pages": len(pages), "exercises": sum(x["exercises"] for x in rows),
            "pairs": sum(x["pairs"] for x in rows), "chapters": rows, "errors": errors}


# Ordered HTML code IDs; a pair supplies the corresponding Python ID automatically.
ORDERS = {
    7: "common-code chain-code open-code extendible-code permutation-code polynomial-code matching-code strings-code puzzle-code basic-code driver-code",
    8: "dsu-code halving-code rollback-code eager-code remove-code lca-code online-code driver-code",
    9: "graph-code heap-code search-code paths-code flow-code mst-code dfs-code low-code euler-code driver-code",
    10: "common-code deadline-code huffman-code packing-code closest-code selection-code arithmetic-code interval-code floyd-code primality-code skip-code turnpike-code game-code sequence-code board-code exercise-huffman exercise-packing exercise-multiply exercise-chain exercise-bst exercise-primality exercise-turnpike exercise-tree circle-pack-code roundrobin-code tournament-path-code convex-hull-code justification-code experiments-code driver-code",
    11: "common-code binomial-code skew-code fibonacci-code binary-code dijkstra-code splay-code mindeque-code driver-code",
    12: "common-code splay-code redblack-code bb-code aa-code treap-code skip-code kd-code kdheap-code pairing-code compact-code nullfree-code checks-code driver-code",
}
# A prefix tuple is (code ID, C stopping marker, Python stopping marker).
TREE_STATS = ("delete-strategy-experiment", "static Node *strategy_delete", "def strategy_delete")
FIND_SHARED = ("list-support", ("SNode", "xmalloc", "node", "append", "dispose_list"),
               ("SNode", "node", "append", "dispose_list"))
RECIPES = {
    "chapter01_selection": (1, ["selection-code", "selection-benchmark"], []),
    "chapter02_loops": (2, ["loop-count-code", "loop-benchmark"], []),
    "chapter02_permutation": (2, ["permutation-code", "permutation-benchmark"], []),
    "chapter03_find": (3, [FIND_SHARED, "list-find-code", "list-search-experiment"],
                       ["-O0", "-fno-optimize-sibling-calls", "-pthread", "-D_POSIX_C_SOURCE=200809L", "-DFIND_EXPERIMENT_MAIN"]),
    "chapter04_delete": (4, ["bst-code", "delete-strategy-experiment"], []),
    "chapter04_splay": (4, ["exercise-splay"], []),
    "chapter04_trees": (4, ["bst-code", "avl-update-core", "tree-builders", "splay-code",
                            TREE_STATS, "tree-performance-experiment"], []),
    "chapter05_build_count": (5, ["build-benchmark-code"], ["-DHEAP_CAPACITY=131072", "-DCOUNT_COMPARISONS=1"]),
    "chapter05_build_time": (5, ["build-benchmark-code"], ["-DHEAP_CAPACITY=131072", "-DCOUNT_COMPARISONS=0"]),
    "chapter05_delete": (5, ["binary-code", "refined-delete-code", "delete-benchmark-code"], ["-DHEAP_CAPACITY=131072"]),
    "chapter06_sorting": (6, "common-code insertion-code shell-code heap-sort-code book-quick-code optimized-code experiment-driver-code".split(), []),
    **{f"chapter{n:02d}": (n, ids.split(), []) for n, ids in ORDERS.items()},
}
LIBRARIES = {
    1: "include-expansion-code intro-recursion print-digits selection-code word-puzzle-code fixed-encoding-code".split(),
    2: "maxsum-code search-gcd-power-code loop-count-code permutation-code polynomial-powers-code horner-code fixed-point-code minimum-positive-code subsequence-variants-code prime-code sieve-code iterative-power-code majority-code majority-vote-code binary-word-puzzle-code one-comparison-search-code".split(),
    3: None,  # all portable blocks, with the shared definitions first
    4: "bst-code avl-code avl-update-core avl-iter-insert avl-direct-double splay-code bst-extra cursor-bst tree-builders random-bst-builder minimal-avl-builder perfect-bst-builder range-query tree-layout-code tree-drawing-code level-order-code btree-reference child-sibling-traversal tree-similarity tree-isomorphism tree-transform-code order-statistic-code threaded-bst-code thread-successor-demo bst-link-demo kd-tree-code".split(),
    5: "binary-code topk-code leftist-code skew-code binomial-code refined-delete-code gonnet-build-code threshold-code bulk-insert-code minmax-c parent-leftist-code fifo-build-code bin-merge-fast-code regular-binomial-code packing-c offset-heap-code".split(),
    6: "common-code insertion-code shell-code heap-sort-code merge-sort-code book-quick-code select-code radix-code optimized-code adversary-code partition-code small-sort-code file-merge-code".split(),
    **{n: ids.split() for n, ids in ORDERS.items()},
}


def c_definitions(source, names):
    """Select named definitions without editing their bodies (3.11 shared part)."""
    header = "\n".join(re.findall(r"^#include[^\n]*", source, re.M)) + "\n"
    pieces = [header]
    for name in names:
        if name == "SNode":
            pieces.append(re.search(r"typedef struct SNode\b[^\n]*", source)[0])
            continue
        match = re.search(r"(?m)^static [^\n]*\b" + name + r"\([^\n]*\)\s*\{", source)
        if match is None:
            raise ValueError(f"missing C definition {name}")
        # Mask literals/comments so braces inside them do not change the depth.
        masked = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                        lambda m: " " * len(m[0]), source, flags=re.S)
        start, depth = masked.index("{", match.start()), 0
        for i in range(start, len(masked)):
            depth += (masked[i] == "{") - (masked[i] == "}")
            if depth == 0:
                pieces.append(source[match.start():i + 1])
                break
    return "\n\n".join(pieces)


def paired_id(page, id, language):
    node = page.codes[id]
    pair = next(a for a in node.ancestors() if a.has_class("code-pair"))
    return next(k for k, n in page.codes.items() if n.attrs["data-language"] == language
                and any(a is pair for a in n.ancestors()))


def combine(page, ids, language):
    pieces = []
    for item in ids:
        id = item[0] if isinstance(item, tuple) else item
        real_id = paired_id(page, id, language)
        source = page.codes[real_id].text()
        if isinstance(item, tuple):
            selection = item[1 if language == "c" else 2]
            if isinstance(selection, tuple):
                if language == "c":
                    source = c_definitions(source, selection)
                else:
                    tree = ast.parse(source)
                    source = "\n\n".join(ast.get_source_segment(source, n) for n in tree.body
                                           if getattr(n, "name", None) in selection)
            else:
                if selection not in source:
                    raise ValueError(f"missing boundary {selection} in {real_id}")
                source = source.split(selection, 1)[0]
        pieces.append(f"{'/*' if language == 'c' else '#'} {page.path.name}#{real_id}{' */' if language == 'c' else ''}\n" + source.rstrip())
    return "\n\n".join(pieces) + "\n"


def extract(pages, output):
    manifest = []
    for p in pages:
        for id, node in p.codes.items():
            code = node.text()
            suffix = "c" if node.attrs["data-language"] == "c" else "py"
            path = output / "blocks" / p.path.stem / f"{id}.{suffix}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(code, encoding="utf-8")
            manifest.append({"page": p.path.name, "id": id, "line": node.line,
                             "sha256": hashlib.sha256(code.encode()).hexdigest(),
                             "output": str(path.relative_to(output))})
    (output / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def command(args, *, input=None, timeout=180):
    r = subprocess.run(args, input=input, text=True, capture_output=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(" ".join(map(str, args)) + "\n" + r.stdout + r.stderr)
    return r.stdout


def build(chapters, output):
    compiler = shutil.which("clang")
    if not compiler:
        raise RuntimeError("clang is required to compile C programs")
    built = []
    for name, (chapter, ids, options) in RECIPES.items():
        p = chapters[chapter]
        paths = []
        for lang, suffix in (("c", "c"), ("python", "py")):
            actual_ids = ["binary-code", "build-benchmark-code"] if lang == "python" and name.startswith("chapter05_build") else ids
            path = output / f"{name}.{suffix}"
            path.write_text(combine(p, actual_ids, lang), encoding="utf-8")
            paths.append(path)
        flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", "-O1", "-g"]
        # The fixed-stack-depth experiment deliberately uses its own frame layout.
        if chapter != 3:
            flags += ["-fsanitize=address,undefined"]
        command([compiler, *flags, *options, str(paths[0]), "-lm", "-o", str(output / name)])
        if name in ("chapter10", "chapter11", "chapter12"):
            command([compiler, *flags, *options, "-DNDEBUG", str(paths[0]), "-lm", "-o", str(output / f"{name}_ndebug")])
        ast.parse(paths[1].read_text(), filename=str(paths[1]))
        built.append(name)
        print(f"built {name}", flush=True)
    return built


def syntax(chapters, output):
    checked, covered = [], set()
    compiler = shutil.which("clang")
    for number, ids in LIBRARIES.items():
        p = chapters[number]
        if ids is None:
            ids = ["list-support"] + [id for id, n in p.codes.items() if n.attrs["data-language"] == "c"
                                      and id not in ("list-support", "list-search-experiment")]
        code = combine(p, ids, "c")
        # Library collections have no driver that calls every static helper.
        path = output / f"library{number:02d}.c"
        path.write_text(code, encoding="utf-8")
        command([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-Wno-unused-function", "-fsyntax-only", str(path)])
        python_library = output / f"library{number:02d}.py"
        python_library.write_text(combine(p, ids, "python"), encoding="utf-8")
        command([sys.executable, "-c", "import runpy,sys; runpy.run_path(sys.argv[1],run_name='weiss_notes_library')",
                 str(python_library)])
        for id in ids:
            covered.add((number, id))
        for id, n in p.codes.items():
            if n.attrs["data-language"] == "python":
                ast.parse(n.text(), filename=f"{p.path.name}#{id}")
        checked.append(number)
        print(f"syntax chapter {number:02d}", flush=True)
    for _, (number, ids, _) in RECIPES.items():
        covered.update((number, item[0] if isinstance(item, tuple) else item) for item in ids)
    missing = [(n, id) for n, p in chapters.items() for id, node in p.codes.items()
               if node.attrs["data-language"] == "c" and (n, id) not in covered]
    if missing:
        raise RuntimeError(f"C fragments not covered by syntax/build: {missing}")
    return {"chapters": checked, "c_blocks": len(covered), "python_blocks": sum(
        n.attrs["data-language"] == "python" for p in chapters.values() for n in p.codes.values()),
        "python_library_definition_loads": checked,
        "library_warning_exception": "unused-function only for collections without complete callers"}


def smoke(output):
    cases = [
        ("chapter04_splay", [], None),
        ("chapter07", ["demo"], None),
        ("chapter08", ["demo"], None),
        ("chapter09", ["dijkstra", "0"], "3 3 1\n0 1 2\n1 2 3\n0 2 7\n"),
        ("chapter10", ["chain"], "3 10 20 30 40\n"),
        ("chapter10", ["lcs"], "dynamic\nprogramming\n"),
        ("chapter11", ["demo"], None),
        ("chapter11", ["graph"], "3 3 0\n0 1 2\n1 2 3\n0 2 7\n"),
        ("chapter12", ["selftest"], None),
    ]
    results = []
    for name, args, data in cases:
        c = command([str(output / name), *args], input=data)
        py = command([sys.executable, str(output / f"{name}.py"), *args], input=data)
        if c != py:
            raise RuntimeError(f"C/Python output differs: {name} {args}\n{c}\n{py}")
        if name == "chapter10" and args == ["chain"] and not c.startswith("18000\n"):
            raise RuntimeError("matrix-chain reference answer must be 18000")
        if name == "chapter10" and args == ["lcs"] and not c.startswith("3\n"):
            raise RuntimeError("the source LCS example has length 3")
        if name in ("chapter07", "chapter11", "chapter12"):
            optimized = command([sys.executable, "-O", str(output / f"{name}.py"), *args], input=data)
            if optimized != py:
                raise RuntimeError(f"Python -O changed {name} {args}")
        if name in ("chapter11", "chapter12"):
            disabled = command([str(output / f"{name}_ndebug"), *args], input=data)
            if disabled != c:
                raise RuntimeError(f"C NDEBUG changed {name} {args}")
        results.append({"program": name, "args": args, "matched": True})
        print(f"smoke {name} {' '.join(args)}", flush=True)
    return results


def regressions(chapters, output):
    """Reproduce the corrected boundary/import/assertion cases from the HTML."""
    compiler = shutil.which("clang")
    results = []

    def run_c(name, chapter, ids, driver, data=None):
        path = output / f"{name}.c"
        path.write_text(combine(chapters[chapter], ids, "c") + driver, encoding="utf-8")
        binary = output / name
        command([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-O1", "-g", "-fsanitize=address,undefined", str(path), "-lm", "-o", str(binary)])
        return command([str(binary)], input=data)

    source = combine(chapters[1], ["print-digits", "fixed-encoding-code"], "python")
    namespace = {}
    exec(source, namespace)
    from io import StringIO
    expected = []
    for sign, magnitude, scale in ((True, 625, 2), (False, 0, 0), (True, 0, 3), (False, 2**64 - 1, 0)):
        out = StringIO()
        namespace["print_fixed_encoding"](sign, magnitude, scale, out)
        expected.append(out.getvalue())
    for magnitude, scale in ((1, -1), (1, True), (1, 0.5), (1, 2**63), (-1, 0), (2**64, 0), (0.5, 0)):
        out = StringIO()
        try:
            namespace["print_fixed_encoding"](False, magnitude, scale, out)
        except ValueError:
            if out.getvalue():
                raise RuntimeError("invalid encoding input wrote partial output")
        else:
            raise RuntimeError("invalid encoding input was accepted")
    actual = run_c("regression_encoding", 1, ["print-digits", "fixed-encoding-code"], r'''
int main(void) {
    if (print_fixed_encoding(false, 1, -1)) return 1;
    if (!print_fixed_encoding(true, 625, 2)) return 1; putchar('\n');
    if (!print_fixed_encoding(false, 0, 0)) return 1; putchar('\n');
    if (!print_fixed_encoding(true, 0, 3)) return 1; putchar('\n');
    if (!print_fixed_encoding(false, UINT64_MAX, 0)) return 1; putchar('\n');
    return 0;
}
''')
    if actual.splitlines() != expected:
        raise RuntimeError("fixed-point encoding differs between languages")
    results.append({"case": "encoding", "valid": 4, "invalid_python": 7, "invalid_c": 1})

    arrays = [list(a) for n in range(7) for a in itertools.product((-2, 0, 3), repeat=n)]
    arrays.append([4, -3, 5, -2, -1, 2, 6, -2])
    reference = [max([0] + [sum(a[i:j]) for i in range(len(a)) for j in range(i + 1, len(a) + 1)]) for a in arrays]
    namespace = {}
    exec(combine(chapters[2], ["maxsum-code"], "python"), namespace)
    for a, answer in zip(arrays, reference):
        if any(namespace[f"maxsum{k}"](a) != answer for k in range(1, 5)):
            raise RuntimeError(f"maximum subsequence sum differs: {a}")
    data = "".join(str(len(a)) + " " + " ".join(map(str, a)) + "\n" for a in arrays)
    actual = run_c("regression_maxsum", 2, ["maxsum-code"], r'''
#include <stdio.h>
int main(void) {
    size_t n; int a[8];
    while (scanf("%zu", &n) == 1) {
        if (n > 8) return 1;
        for (size_t i=0; i<n; ++i) if (scanf("%d", &a[i]) != 1) return 1;
        printf("%lld %lld %lld %lld\n", maxsum1(a,n), maxsum2(a,n), maxsum3(a,n), maxsum4(a,n));
    }
    return 0;
}
''', data)
    if [list(map(int, row.split())) for row in actual.splitlines()] != [[x]*4 for x in reference]:
        raise RuntimeError("C maximum subsequence sums differ from the independent reference")
    results.append({"case": "maxsum", "arrays": len(arrays), "algorithms_per_language": 4})

    code = combine(chapters[3], ["list-support", "infix-postfix"], "python")
    namespace = {}
    exec(code, namespace)  # the postfix evaluator is deliberately absent
    if namespace["infix_postfix"](["1.25", "+", "2", "^", "3", "^", "4"]) != ["1.25", "2", "3", "4", "^", "^", "+"]:
        raise RuntimeError("infix conversion precedence differs")
    for tokens in ([], ["("], ["1", "2"], ["1e999"], ["1", "+"]):
        try:
            namespace["infix_postfix"](tokens)
        except ValueError:
            pass
        else:
            raise RuntimeError(f"infix conversion accepted invalid tokens: {tokens}")
    shared = ("list-support", ("xcalloc", "number_token"), ("number_token",))
    actual = run_c("regression_infix", 3, [shared, "infix-postfix"], r'''
int main(void) {
    const char *input[]={"1.25", "+", "2", "^", "3", "^", "4"}, *out[7]; size_t n=0;
    if (!infix_postfix(input,7,out,&n) || n!=7) return 1;
    for (size_t i=0; i<n; ++i) printf("%s%s", i ? " " : "", out[i]); putchar('\n');
    const char *bad[]={"1", "+"};
    if (infix_postfix(bad,2,out,&n) || n!=0) return 1;
    if (infix_postfix(input,0,out,&n) || n!=0) return 1;
    return 0;
}
''')
    if actual != "1.25 2 3 4 ^ ^ +\n":
        raise RuntimeError("C infix conversion differs")
    results.append({"case": "infix_without_postfix_import", "valid": 1, "invalid_python": 5, "invalid_c": 2})

    source = combine(chapters[3], [FIND_SHARED, "list-find-code", "list-search-experiment"], "python")
    source += '''
from contextlib import redirect_stdout
from io import StringIO
counts = [0, 0]
original_iter, original_rec = find_iter, find_rec
def counted_iter(head, key):
    counts[0] += 1
    return original_iter(head, key)
def counted_rec(head, key):
    counts[1] += 1
    # Keep recursive calls bound to the original implementation.
    globals()['find_rec'] = original_rec
    try: return original_rec(head, key)
    finally: globals()['find_rec'] = counted_rec
find_iter, find_rec = counted_iter, counted_rec
recursive_probe = lambda n, limit: 77 if n >= 998 else 0
with redirect_stdout(StringIO()): run_find_experiment()
if counts != [600, 600]: raise RuntimeError(f'benchmark calls disappeared: {counts}')
print('600 600')
'''
    path = output / "regression_find.py"
    path.write_text(source, encoding="utf-8")
    normal = command([sys.executable, str(path)])
    optimized = command([sys.executable, "-O", str(path)])
    if normal != "600 600\n" or optimized != normal:
        raise RuntimeError("Python optimization removed measured list searches")
    results.append({"case": "find_calls", "calls_per_method": 600, "python_modes": ["default", "-O"],
                    "depth_probe": "stubbed; this check measures invocation preservation"})
    print("targeted boundary/import/optimization regressions passed", flush=True)
    return results


def benchmarks(chapters, output):
    """Compare deterministic results; historical timing values remain in the book."""
    cases = [(7, mode) for mode in ("collisions", "memory", "puzzle")]
    cases += [(11, "bench")] + [(12, mode) for mode in ("splay", "trees", "priority", "heaps", "bad")]
    result = []
    for number, mode in cases:
        name = f"chapter{number:02d}"
        c = command([str(output / name), mode])
        py = command([sys.executable, str(output / f"{name}.py"), mode])
        optimized = command([sys.executable, "-O", str(output / f"{name}.py"), mode])
        for suffix, data in (("c", c), ("python", py)):
            (output / f"{name}-{mode}-{suffix}.csv").write_text(data, encoding="utf-8")
        if number == 7:
            skip = {"collisions": {9}, "memory": {3, 4}, "puzzle": {4}}[mode]
            def normalized(text):
                return [[value for i, value in enumerate(row) if i not in skip]
                        for row in csv.reader(io.StringIO(text))]
            if normalized(c) != normalized(py) or normalized(c) != normalized(optimized):
                raise RuntimeError(f"benchmark operations differ: {name} {mode}")
            count = len(normalized(c))
        else:
            def normalized(text):
                return [{key: value for key, value in row.items() if key != "ms"}
                        for row in csv.DictReader(io.StringIO(text))]
            current = normalized(c)
            disabled = command([str(output / f"{name}_ndebug"), mode])
            if any(normalized(other) != current for other in (py, optimized, disabled)):
                raise RuntimeError(f"benchmark operations differ: {name} {mode}")
            if number == 11:
                table_id = "benchmark-source-chapter11-0"
                columns = [0, 1, 4, 5, 6, 7, 10]
                keys = ["V", "E", "comparisons", "links", "cuts", "decreases", "hash"]
            else:
                index = {"splay": 0, "trees": 1, "priority": 2, "heaps": 3, "bad": 4}[mode]
                table_id = f"benchmark-source-chapter12-{index}"
                columns = [0, 3, 4, 5, 6, 7, 10]
                keys = ["N", "operations", "comparisons", "rotations", "visits", "links", "checksum"]
            table = chapters[number].ids[table_id]
            historical = []
            for row in chapters[number].nodes:
                if row.tag != "tr" or not any(a is table for a in row.ancestors()):
                    continue
                cells = [td.text().strip().replace(",", "") for td in row.parts
                         if isinstance(td, Node) and td.tag == "td"]
                if cells:
                    historical.append(tuple(int(cells[i]) for i in columns))
            if Counter(historical) != Counter(tuple(int(row[key]) for key in keys) for row in current):
                raise RuntimeError(f"recorded work counts differ: {name} {mode}")
            count = len(current)
        result.append({"chapter": number, "mode": mode, "rows": count,
                       "c_python_optimized_match": True, "historical_counts_match": number != 7})
        print(f"benchmark {name} {mode}: {count} rows", flush=True)
    return result


def chapter10_exercises(chapters, output):
    """Check exercise drivers and new algorithms against small independent oracles."""
    p = chapters[10]
    ns = {"__name__": "weiss_notes_library"}
    exec(combine(p, ORDERS[10].split(), "python"), ns)
    demos = (3, 10, 22, 28, 31, 39, 41, 43, 46, 48, 49, 51, 52)
    demo_outputs = {}
    for number in demos:
        args = [f"ex10-{number}"]
        c = command([str(output / "chapter10"), *args])
        variants = [command([str(output / "chapter10_ndebug"), *args]),
                    command([sys.executable, str(output / "chapter10.py"), *args]),
                    command([sys.executable, "-O", str(output / "chapter10.py"), *args])]
        if any(value != c for value in variants):
            raise ValueError(f"exercise 10.{number} differs between languages/optimization modes")
        demo_outputs[number] = c
    for number, fragment in ((3, "bits,12914"), (22, "result,5332114"), (28, "cost 1150"),
                             (31, "cost 214"), (39, "2^340_mod_341,1"),
                             (43, "prune 1 value 68 leaves 13"), (52, "cost 4")):
        if fragment not in demo_outputs[number]:
            raise ValueError(f"exercise 10.{number} misses its reference result")
    codes = [row.split(",")[2] for row in demo_outputs[3].splitlines()[1:-1]]
    if any(a.startswith(b) for i, a in enumerate(codes) for j, b in enumerate(codes) if i != j):
        raise ValueError("the exercise Huffman code is not prefix-free")
    packing_lines = demo_outputs[10].splitlines()
    sizes = [42,25,27,7,72,86,9,44,50,68,73,31,78,17,79,37,73,23,30]
    for mode, bins in enumerate((12,10,10,10,10)):
        if int(packing_lines[2*mode].split()[-1]) != bins:
            raise ValueError("the book packing example has an unexpected bin count")
        loads = [0]*bins
        for size, assigned in zip(sizes, map(int, packing_lines[2*mode+1].split())):
            loads[assigned-1] += size
        if max(loads) > 100:
            raise ValueError("exercise packing exceeds bin capacity")
    points = [tuple(map(int, row.split())) for row in demo_outputs[41].splitlines()[1:5]]
    distances = [1,2,3,4,5,6,7,8,9,10,11,12,13,16,17]
    if len(set(points)) != 4 or any(sorted(b-a for i,a in enumerate(row) for b in row[i+1:]) != distances for row in points):
        raise ValueError("the homometric enumeration does not match the original distances")

    # One batch keeps thousands of small inputs in a single Sanitizer process.
    ids = "common-code closest-code arithmetic-code circle-pack-code roundrobin-code tournament-path-code convex-hull-code justification-code".split()
    harness = r'''
int test_int(void) {
    int value;
    if(scanf("%d",&value)!=1) fail("missing test integer");
    return value;
}
int main(void) {
    int mode;
    while(scanf("%d",&mode)==1) {
        int n=test_int(),width=test_int(),blank=test_int();
        if(mode<2) {
            int *a=alloc((size_t)n,sizeof *a),*end=alloc((size_t)n,sizeof *end);
            for(int i=0;i<n;i++) a[i]=test_int();
            int64_t total; int ok=mode?justify_printer(a,n,width,&total,end):justify_dp(a,n,width,blank,&total,end);
            printf("%d",ok);
            if(ok) { printf(" %" PRId64,total); for(int i=0;i<n;i=end[i]) printf(" %d",end[i]); }
            putchar('\n'); free(a); free(end);
        } else if(mode==2) {
            Point *a=alloc((size_t)n,sizeof *a),*hull=alloc((size_t)2*n,sizeof *hull);
            for(int i=0;i<n;i++) { int x=test_int(),y=test_int(); a[i]=(Point){x,y,i}; }
            int count=convex_hull(a,n,hull); printf("%d",count);
            for(int i=0;i<count;i++) printf(" %d %d",hull[i].x,hull[i].y);
            putchar('\n'); free(a); free(hull);
        } else if(mode==3) {
            unsigned char *win=alloc((size_t)n*(size_t)n,sizeof *win);
            for(int i=0;i<n*n;i++) win[i]=(unsigned char)test_int();
            tournament_check(win,n); int *path=tournament_path(win,n);
            printf("%d",n); for(int i=0;i<n;i++) printf(" %d",path[i]);
            putchar('\n'); free(win); free(path);
        } else if(mode==4) {
            printf("%" PRId64 "\n",karatsuba(width,blank));
        } else if(mode==5) {
            double *r=alloc((size_t)n,sizeof *r),*x=alloc((size_t)n,sizeof *x);
            for(int i=0;i<n;i++) if(scanf("%lf",&r[i])!=1) fail("missing radius");
            double result=circle_pack(r,n,x); printf("%.17g",result);
            for(int i=0;i<n;i++) printf(" %.17g",x[i]);
            putchar('\n'); free(r); free(x);
        } else if(mode==6) {
            int *a=round_robin(n); unsigned char *seen=alloc((size_t)n*(size_t)n,1);
            uint64_t hash=0;
            for(int d=0;d<n-1;d++) for(int i=0;i<n;i++) {
                int j=a[d*n+i];
                if(j<0 || j>=n || j==i || a[d*n+j]!=i || seen[i*n+j]) fail("invalid schedule");
                seen[i*n+j]=1; hash=hash*131+(uint64_t)j;
            }
            printf("%d %" PRIu64 "\n",n,hash); free(a); free(seen);
        } else fail("unknown test mode");
    }
    return ferror(stdin)?1:0;
}
'''
    source = output / "chapter10_exercise_checks.c"
    source.write_text(combine(p, ids, "c") + harness, encoding="utf-8")
    executable = output / "chapter10_exercise_checks"
    command([shutil.which("clang"), "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
             "-O1", "-g", "-fsanitize=address,undefined", str(source), "-lm", "-o", str(executable)])
    inputs, expected, kinds = [], [], Counter()

    def case(kind, n, width, blank, fields, result):
        inputs.append(" ".join(map(str, (kind,n,width,blank,*fields))))
        expected.append(result); kinds[kind] += 1

    def layout_result(result, n):
        if result is None: return [0]
        cost, end = result; breaks = []; i = 0
        while i < n:
            if not i < end[i] <= n: raise ValueError("invalid layout reconstruction")
            i = end[i]; breaks.append(i)
        return [1,cost,*breaks]

    def partition_oracle(a, width, blank, printer):
        if not a: return [1,0]
        best = None; n = len(a)
        for mask in range(1 << (n-1)):
            breaks = [i+1 for i in range(n-1) if mask & (1 << i)] + [n]
            cost = 0; start = 0
            for end in breaks:
                words = sum(a[start:end]); gaps = end-start-1; last = end == n
                if not gaps:
                    if words > width or (not last and words != width): break
                elif words >= width or (printer and words+gaps > width): break
                else:
                    deviation = gaps*blank-(width-words)
                    cost += max(0,deviation) if last else abs(deviation)
                start = end
            else:
                value = (cost,tuple(breaks))
                if best is None or value < best: best = value
        return [0] if best is None else [1,best[0],*best[1]]

    rng = random.Random(20261004)
    layouts = [(list(a), width, blank) for n in range(6)
               for a in itertools.product((1,2,3), repeat=n) for width in range(1,7) for blank in range(1,4)]
    layouts += [([rng.randint(1,15) for _ in range(rng.randint(0,8))],rng.randint(1,25),rng.randint(1,8)) for _ in range(200)]
    layouts += [([10**9,10**9,1],10**9,10**9), ([1,1,1,1],10**9,10**9),
                ([1,4,1,8,2],10,1), ([4,4,4],9,2)]
    for a, width, blank in layouts:
        ref = partition_oracle(a,width,blank,False)
        if layout_result(ns["justify_dp"](a,width,blank),len(a)) != ref:
            raise ValueError(f"layout DP disagrees with partition enumeration: {a}, {width}, {blank}")
        case(0,len(a),width,blank,a,ref)
        if blank == 1:
            ref = partition_oracle(a,width,1,True)
            if layout_result(ns["justify_printer"](a,width),len(a)) != ref:
                raise ValueError(f"linear printer disagrees with partition enumeration: {a}, {width}")
            case(1,len(a),width,1,a,ref)
    a = [1]*100000; ref = [1,0,*range(2,100001,2)]
    if layout_result(ns["justify_printer"](a,3),len(a)) != ref:
        raise ValueError("linear printer failed the 100000-word input")
    case(1,len(a),3,1,a,ref)

    def wrapping_oracle(points):
        a = sorted(set(points))
        if len(a) < 2: return a
        out = []; current = a[0]
        while True:
            out.append(current); nxt = next(p for p in a if p != current)
            for pnt in a:
                if pnt == current: continue
                cross = (nxt[0]-current[0])*(pnt[1]-current[1])-(nxt[1]-current[1])*(pnt[0]-current[0])
                dist = lambda p: (p[0]-current[0])**2+(p[1]-current[1])**2
                if cross < 0 or (cross == 0 and dist(pnt) > dist(nxt)): nxt = pnt
            current = nxt
            if current == out[0]: return out
            if len(out) > len(a): raise ValueError("convex-hull oracle failed to close")

    grid = list(itertools.product(range(3), repeat=2))
    hulls = [[grid[i] for i in range(9) if mask & (1 << i)] for mask in range(512)]
    hulls += [[(rng.randint(-10,10),rng.randint(-10,10)) for _ in range(rng.randint(0,30))] for _ in range(150)]
    hulls += [[(-1000000,-1000000),(1000000,-1000000),(1000000,1000000),(-1000000,1000000),(0,0)],
              [(1,1)]*10, [(i,2*i) for i in range(100)]]
    for points in hulls:
        ref = wrapping_oracle(points)
        actual = [(x,y) for x,y,_ in ns["convex_hull"]([(x,y,i) for i,(x,y) in enumerate(points)])]
        if actual != ref: raise ValueError(f"convex hull disagrees with gift wrapping: {points}")
        case(2,len(points),0,0,itertools.chain.from_iterable(points),[len(ref),*itertools.chain.from_iterable(ref)])

    def tournament_case(win):
        n = len(win); ns["tournament_check"](win); path = ns["tournament_path"](win)
        if sorted(path) != list(range(n)) or any(win[a][b] != 1 for a,b in zip(path,path[1:])):
            raise ValueError("tournament path is not a permutation of adjacent winners")
        case(3,n,0,0,itertools.chain.from_iterable(win),[n,*path])

    for n in range(6):
        pairs = list(itertools.combinations(range(n),2))
        for mask in range(1 << len(pairs)):
            win = [[0]*n for _ in range(n)]
            for k,(i,j) in enumerate(pairs): win[i][j] = (mask >> k)&1; win[j][i] = 1-win[i][j]
            tournament_case(win)
    for _ in range(30):
        n = rng.randint(6,100); win = [[0]*n for _ in range(n)]
        for i,j in itertools.combinations(range(n),2): win[i][j] = rng.randrange(2); win[j][i] = 1-win[i][j]
        tournament_case(win)
    products = list(itertools.product((-10**9,-10,-1,0,1,10,10**9), repeat=2))
    products += [(rng.randint(-10**9,10**9),rng.randint(-10**9,10**9)) for _ in range(1000)]
    for x,y in products:
        if ns["karatsuba"](x,y) != x*y: raise ValueError("Karatsuba disagrees with integer multiplication")
        case(4,0,x,y,[],[x*y])

    def integer_circle_oracle(r):
        if not r: return 0,[]
        best = (2*sum(r)+1,())
        def search(x):
            nonlocal best
            i = len(x)
            if i == len(r):
                best = min(best,(max(v+rad for v,rad in zip(x,r)),tuple(x))); return
            for v in range(max(r[i],x[-1] if x else 0),best[0]-r[i]+1):
                if all((v-old)**2+(r[i]-r[j])**2 >= (r[i]+r[j])**2 for j,old in enumerate(x)):
                    search(x+[v])
        search([]); return best[0],list(best[1])

    circles = [list(r) for n in range(4) for r in itertools.product((1,4,9),repeat=n)]
    for r in circles:
        ref_width,ref_center = integer_circle_oracle(r)
        width,center = ns["circle_pack"](r)
        if width != ref_width or center != ref_center: raise ValueError("circle packing disagrees with integer-position enumeration")
        case(5,len(r),0,0,r,[width,*center])
    circles = [[2,1,2],[0.000001,1000000,0.000001], [1000000]*12]
    circles += [[rng.uniform(0.1,10) for _ in range(rng.randint(1,12))] for _ in range(40)]
    for r in circles:
        width,center = ns["circle_pack"](r)
        if any(x+1e-8 < rad or x+rad > width+1e-8 for x,rad in zip(center,r)):
            raise ValueError("circle packing crosses a box boundary")
        for i,x in enumerate(center):
            for j in range(i):
                distance = (x-center[j])**2+(r[i]-r[j])**2
                if distance+1e-8*max(1,distance) < (r[i]+r[j])**2: raise ValueError("circle packing overlaps")
        case(5,len(r),0,0,r,[width,*center])
    for k in range(11):
        n = 1 << k; opponent = ns["round_robin"](n); seen = set(); value = 0
        if len(opponent) != n-1: raise ValueError("wrong tournament day count")
        for row in opponent:
            if len(row) != n: raise ValueError("wrong player count")
            for i,j in enumerate(row):
                if j == i or not 0 <= j < n or row[j] != i or (i,j) in seen:
                    raise ValueError("a player repeats or misses a tournament match")
                seen.add((i,j)); value = (value*131+j) & ((1 << 64)-1)
        if len(seen) != n*(n-1): raise ValueError("not all tournament pairs were scheduled")
        case(6,n,0,0,[],[n,value])
    actual = command([str(executable)],input="\n".join(inputs)+"\n",timeout=180).splitlines()
    if len(actual) != len(expected): raise ValueError("exercise batch output count differs")
    for index,(line,ref) in enumerate(zip(actual,expected)):
        numbers = list(map(float if inputs[index].startswith("5 ") else int,line.split()))
        good = len(numbers) == len(ref) and all(math.isclose(a,b,rel_tol=5e-14,abs_tol=1e-10) if inputs[index].startswith("5 ") else a == b for a,b in zip(numbers,ref))
        if not good: raise ValueError(f"C exercise batch differs from independent result at {index}: {line}; {ref}")
    # Check the recovered fractional/integer blanks, not only the DP value.
    from fractions import Fraction
    spacing = [(False,[1,4,1,8,2],10,1), (True,[1,4,1,8,2],10,1),
               (False,[4,4,4],9,2), (False,[1,1,1,10],10,1),
               (True,[1,1,1,10],10,1), (False,[1,1],3,10),
               (False,[10,1],10,1), (True,[11],10,1), (True,[],10,1)]
    for printer,a,width,blank in spacing:
        mode = "printer" if printer else "justify"
        data = " ".join(map(str,([len(a),width] if printer else [len(a),width,blank])+a))
        c = command([str(output / "chapter10"),mode],input=data)
        py = command([sys.executable,str(output / "chapter10.py"),mode],input=data)
        if c != py: raise ValueError("recovered layout blanks differ between languages")
        ref = partition_oracle(a,width,blank,printer)
        if ref == [0]:
            if c != "impossible\n": raise ValueError("infeasible layout was printed")
            continue
        rows = c.splitlines(); cost = int(rows.pop(0).split()[1]); i = 0; measured = Fraction(0)
        breaks = []
        while rows:
            label,first,last = rows.pop(0).split(); first,last = int(first)-1,int(last)
            if label != "line" or first != i or not first < last <= len(a): raise ValueError("invalid printed line bounds")
            gaps = last-first-1; blanks = []
            if gaps:
                fields = rows.pop(0).split()
                if fields[0] != "blanks": raise ValueError("missing printed blank widths")
                blanks = list(map(Fraction,fields[1:]))
                if len(blanks) != gaps or any(x <= 0 for x in blanks): raise ValueError("invalid printed blanks")
                if printer and any(x.denominator != 1 or x < 1 for x in blanks): raise ValueError("printer blanks must be positive integers")
            filled = sum(a[first:last])+sum(blanks)
            if filled > width or (last != len(a) and filled != width): raise ValueError("printed line does not fit its width")
            measured += sum(max(0,blank-x) if last == len(a) else abs(x-blank) for x in blanks)
            breaks.append(last); i = last
        if i != len(a) or measured != cost or [1,cost,*breaks] != ref:
            raise ValueError("printed blanks fail to attain the optimal layout cost")
    bad = [("circle","1 0"),("circle","1 nan"),("circle","1 1e-12"),("circle","1 1000001"),
           ("circle","1 1_0"),("circle","1 ١"),
           ("roundrobin","0"),("roundrobin","3"),("roundrobin","1025"),
           ("tournament","2 0 1 1 0"),("tournament","2 0 0 0 0"),("tournament","1 1"),
           ("hull","1 1000001 0"),("justify","1 10 1 0"),("justify","1 0 1 1"),
           ("justify","1 10 0 1"),("justify","5001 1 1"),("printer","100001 1"),
           ("hull","1 0"),("printer","0 10 extra")]
    for mode,data in bad:
        for program in ([str(output / "chapter10"),mode], [sys.executable,str(output / "chapter10.py"),mode]):
            result = subprocess.run(program,input=data,text=True,capture_output=True,timeout=30)
            if result.returncode == 0: raise ValueError(f"invalid exercise input accepted: {mode} {data}")
            if "ERROR: AddressSanitizer" in result.stderr or "runtime error:" in result.stderr:
                raise ValueError(f"invalid exercise input triggered a memory/undefined-behavior error: {mode}")
    report = {"drivers": len(demos), "driver_modes": "C, C NDEBUG, Python, Python -O",
              "layout_dp_partitions": kinds[0], "linear_printer_partitions": kinds[1]-1,
              "linear_printer_large_words": 100000, "hull_gift_wrapping": kinds[2],
              "tournament_winner_paths": kinds[3], "karatsuba_integer_products": kinds[4],
              "circle_cases": kinds[5], "circle_integer_position_enumerations": 40,
              "round_robin_player_counts": [1 << k for k in range(11)],
              "invalid_input_cases": len(bad), "batch_cases": len(expected),
              "layout_spacing_reconstructions": len(spacing),
              "c_memory_checks": "AddressSanitizer and UndefinedBehaviorSanitizer"}
    print(f"chapter 10 exercises: {len(demos)} paired drivers, {len(expected)} independent cases passed",flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", type=Path, metavar="DIR", help="extract all code blocks and a source/hash manifest")
    parser.add_argument("--verify", type=Path, metavar="DIR", help="extract, compile all C collections/17 programs, and run selected C/Python checks")
    parser.add_argument("--benchmarks", action="store_true", help="with --verify, compare the 145 rows from chapter 7/11/12 experiments and assertion-disabled variants")
    args = parser.parse_args()
    if args.benchmarks and not args.verify:
        parser.error("--benchmarks requires --verify DIR")
    pages = [Page(p.resolve()) for p in sorted(NOTES.glob("*.html"))]
    report = check(pages)
    report["checked_at"] = datetime.now(timezone.utc).isoformat()
    report["python"] = sys.version.split()[0]
    report["platform"] = platform.platform()
    report["source_pages"] = [{"file": p.path.name, "sha256": hashlib.sha256(p.path.read_bytes()).hexdigest()}
                              for p in pages]
    if report["errors"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    print(f"HTML: {report['pages']} pages, {report['exercises']} exercises, {report['pairs']} C/Python pairs; no structural errors", flush=True)
    output = args.verify or args.extract
    if output:
        output = output.resolve()
        if output in (NOTES, NOTES.parent):
            parser.error("choose a dedicated output directory")
        output.mkdir(parents=True, exist_ok=True)
        report["status"] = "running"
        evidence = output / "validation.json"
        evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["extracted_blocks"] = len(extract(pages, output))
        if args.verify:
            chapters = {int(re.match(r"chapter(\d+)_", p.path.name)[1]): p for p in pages if p.path.name.startswith("chapter")}
            try:
                report["builds"] = build(chapters, output)
                report["syntax"] = syntax(chapters, output)
                report["smoke"] = smoke(output)
                report["regressions"] = regressions(chapters, output)
                report["chapter10_exercises"] = chapter10_exercises(chapters, output)
                if args.benchmarks:
                    report["benchmarks"] = benchmarks(chapters, output)
            except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                report["status"] = "failed"
                report["errors"].append(str(error))
                evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(str(error), file=sys.stderr)
                return 1
        report["status"] = "passed"
        evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"evidence: {evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
