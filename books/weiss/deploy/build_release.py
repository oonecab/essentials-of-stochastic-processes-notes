#!/usr/bin/env python3
"""Package the canonical notes for the self-hosted Weiss static site."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import unquote, urljoin, urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "notes"


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.references = []
        self.current = None
        self.events = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.events.extend(key for key in attrs if key.startswith("on"))
        if tag == "script":
            if attrs.get("src"):
                raise ValueError("The release must use self-contained inline scripts")
            self.current = ""
        for key in ("src", "href", "poster"):
            if key in attrs:
                self.references.append((tag, attrs[key]))

    def handle_data(self, data):
        if self.current is not None:
            self.current += data

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.scripts.append(self.current)
            self.current = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-id", default=datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S"))
    args = parser.parse_args()
    if not re.fullmatch(r"\d{8}T\d{6}", args.release_id):
        parser.error("release ID must be YYYYMMDDTHHMMSS")
    out = ROOT / "deploy" / "releases" / args.release_id
    if out.exists():
        parser.error(f"release already exists: {out}")

    paths = sorted(NOTES.glob("*.html"))
    if len(paths) != 13 or not (NOTES / "book_overview.html").is_file():
        raise ValueError("Expected the book overview and all twelve chapter pages")
    release_paths = paths + [NOTES / "README.md", NOTES / "tools" / "check_notes.py"]
    sources = {p.relative_to(NOTES).as_posix(): p for p in release_paths}
    sources["c/ch8.c"] = ROOT / "c" / "ch8.c"
    blobs = {name: p.read_bytes() for name, p in sources.items()}
    sys.path.insert(0, str(NOTES / "tools"))
    import check_notes
    validation = check_notes.check([check_notes.Page(p) for p in paths])
    if validation["errors"]:
        raise ValueError(validation["errors"])

    scripts = set()
    for name, blob in blobs.items():
        scan = Resources()
        if not name.endswith(".html"):
            continue
        scan.feed(blob.decode("utf-8"))
        if scan.events:
            raise ValueError(f"{name}: inline event handlers need explicit CSP handling")
        for tag, ref in scan.references:
            url = urlsplit(ref)
            if tag != "a" and (url.netloc or url.scheme not in ("", "data")):
                raise ValueError(f"{name}: external resource {ref}")
            target = unquote(urlsplit(urljoin("https://weiss.zzzping.top/" + name, ref)).path).lstrip("/")
            if not url.netloc and not url.scheme and url.path and target not in blobs:
                raise ValueError(f"{name}: resource outside the HTML release: {ref}")
        scripts.update(scan.scripts)
    with tempfile.TemporaryDirectory(prefix="weiss-js-check-") as temp:
        for i, script in enumerate(sorted(scripts)):
            path = Path(temp) / f"inline-{i}.js"
            path.write_text(script, encoding="utf-8")
            subprocess.run(["node", "--check", str(path)], check=True)
    for name, path in sources.items():
        if path.read_bytes() != blobs[name]:
            raise RuntimeError(f"Source changed while packaging: {path}")

    out.mkdir(parents=True)
    archive = out / "site.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name, blob in blobs.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.uid, info.gid, info.mtime = len(blob), 0o644, 0, 0, 0
            tar.addfile(info, io.BytesIO(blob))
    records = [{"path": name, "source_path": sources[name].relative_to(ROOT).as_posix(), "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()} for name, blob in blobs.items()]
    script_sources = ["'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'" for s in sorted(scripts)]
    metadata = {
        "release_id": args.release_id,
        "created_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "server": "39.106.147.77",
        "domain": "weiss.zzzping.top",
        "source_directory": str(NOTES),
        "entry_point": "book_overview.html",
        "files": records,
        "total_bytes": sum(x["bytes"] for x in records),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "inline_script_csp_sources": script_sources,
        "validation": validation,
        "inline_script_syntax_check": "passed",
    }
    (out / "release.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    (out / "SHA256SUMS").write_text("".join(f"{x['sha256']}  {x['path']}\n" for x in records))
    (out / "archive.sha256").write_text(f"{metadata['archive_sha256']}  site.tar.gz\n")
    template = (ROOT / "deploy" / "nginx-weiss.zzzping.top.conf.template").read_text()
    config = template.replace("@@ACCESS_POLICY@@", "# Public access requested by the site owner.")
    config = config.replace("@@CACHE_POLICY@@", "no-cache").replace("@@SCRIPT_SOURCES@@", " ".join(script_sources))
    (out / "nginx-weiss.zzzping.top.conf").write_text(config)
    (ROOT / "deploy" / "nginx-weiss.zzzping.top.conf").write_text(config)
    print(json.dumps({"release_id": args.release_id, "directory": str(out), "pages": len(paths), "files": len(records), "bytes": metadata["total_bytes"], "archive_bytes": archive.stat().st_size, "csp_script_sources": script_sources, "validation": {k: v for k, v in validation.items() if k != "chapters"}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
