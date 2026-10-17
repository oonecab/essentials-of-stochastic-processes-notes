#!/usr/bin/env python3
"""Independently inventory numbered source items; never infer them from notes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
KINDS = r"Observation|Rule|Definition|Theorem|Lemma|Corollary|Example|Exercise"
CHAPTER_STARTS = [3, 11, 25, 41, 63, 97, 117, 157, 193, 221]
EXERCISE_STARTS = [7, 21, 37, 52, 87, 108, 147, 179, 217, 252]


def inventory(source):
    run = subprocess.run(["pdftotext", "-layout", str(source), "-"],
                         capture_output=True, text=True, check=True)
    pages = run.stdout.split("\f")
    if not pages[-1].strip():
        pages.pop()
    items, labels, references = {}, [], []
    for pdf, text in enumerate(pages, 1):
        match = re.search(r"master.*?\bpage ([ivxlcdm]+|\d+)\s*(?:\||---)", text)
        printed = match[1] if match else None
        labels.append({"pdf_page": pdf, "printed_page": printed})
        if printed is None or not printed.isdecimal() or not 3 <= int(printed) <= 260:
            continue
        chapter = max(i + 1 for i, start in enumerate(CHAPTER_STARTS) if start <= int(printed))
        for match in re.finditer(r"^\s*(" + KINDS + r")\s+(\d+\.\d+)(?:\s*(\([^\n]*?\)))?\.", text, re.M):
            kind, number, title = match.groups()
            if int(number.split('.')[0]) != chapter or (kind == 'Exercise' and
                    int(printed) < EXERCISE_STARTS[chapter - 1]):
                continue
            key = (kind, number)
            item = {"kind": kind, "number": number, "printed_page": int(printed),
                    "pdf_page": pdf, "review_status": "pending"}
            if key in items:
                # A named formal statement supersedes the same-page forward
                # reference (Definition 7.1); later wrapped references do not.
                if title and kind != 'Exercise':
                    references.append(items[key])
                    items[key] = item
                else:
                    references.append(item)
            else:
                items[key] = item
    # Radical glyphs split this label across lines in Poppler's text layer.
    # Its identity and position are checked on the rendered source page.
    items[('Exercise', '10.10')] = {"kind": "Exercise", "number": "10.10",
        "printed_page": 255, "pdf_page": 270, "review_status": "pending",
        "extraction_note": "Label split by radical glyphs; transcribed from source page"}
    for chapter in range(1, 11):
        nums = sorted(int(number.split('.')[1]) for kind, number in items
                      if kind == 'Exercise' and number.startswith(str(chapter) + '.'))
        if nums != list(range(1, max(nums) + 1)):
            raise ValueError(f"Noncontiguous source exercise inventory: chapter {chapter}")
    return {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "pdf_pages": len(pages), "page_labels": labels,
            "scope": "Numbered items in printed pages 1–260, excluding repeated appendix answers",
            "limitations": "Raw text-layer inventory; pending here means extraction alone does not perform visual or semantic review. Preserve separately verified review metadata when updating the maintained inventory.",
            "excluded_wrapped_references": references,
            "items": sorted(items.values(), key=lambda item: (item['pdf_page'], item['kind'],
                            int(item['number'].split('.')[1])))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "tmp/source.pdf")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = inventory(args.source)
    if args.write:
        (ROOT / "notes/source_inventory.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    counts = {kind: sum(item["kind"] == kind for item in data["items"])
              for kind in sorted({item["kind"] for item in data["items"]})}
    print(json.dumps({"pages": data["pdf_pages"], "counts": counts,
                      "chapter_exercises": {str(c): sum(item["kind"] == "Exercise" and
                        item["number"].startswith(str(c) + ".") for item in data["items"])
                        for c in range(1, 11)}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
