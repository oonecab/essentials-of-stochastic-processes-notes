"""Read the repository's book registry with safe, relative source paths."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]


def local_path(base: Path, name: str) -> Path:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"Unsafe registry path: {name!r}")
    target = base / name
    if target.resolve() != base.resolve() and base.resolve() not in target.resolve().parents:
        raise ValueError(f"Registry path leaves its directory: {name!r}")
    return target


def load_books() -> dict[str, dict]:
    data = json.loads((ROOT / "books/catalog.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not data.get("books"):
        raise ValueError("Expected a nonempty version-1 book registry")
    books, prefixes = {}, set()
    for book in data["books"]:
        key, prefix = book["id"], book["publish_prefix"]
        if not re.fullmatch(r"[a-z][a-z0-9-]*", key) or key in books:
            raise ValueError(f"Invalid or repeated book ID: {key}")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", prefix) or prefix in prefixes:
            raise ValueError(f"Invalid or repeated publication prefix: {prefix}")
        base = local_path(ROOT, book["directory"])
        if not base.is_dir():
            raise ValueError(f"Missing book directory: {book['directory']}")
        for field in ("entry", "guidelines", "checker"):
            if not local_path(base, book[field]).is_file():
                raise ValueError(f"Missing {key} {field}: {book[field]}")
        for field in ("notes_directory", "code_directory"):
            if not local_path(base, book[field]).is_dir():
                raise ValueError(f"Missing {key} directory: {book[field]}")
        pages = list((base / book["notes_directory"]).glob("*.html"))
        if len(pages) != book["expected_pages"]:
            raise ValueError(f"{key}: expected {book['expected_pages']} pages, found {len(pages)}")
        books[key] = {**book, "root": base}
        prefixes.add(prefix)
    return books
