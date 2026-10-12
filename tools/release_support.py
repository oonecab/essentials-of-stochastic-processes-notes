"""Verify and unpack a release without trusting archive member paths."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def extract_release(release: Path, destination: Path) -> dict:
    metadata = json.loads((release / "release.json").read_text(encoding="utf-8"))
    archive = release / "site.tar.gz"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != metadata["archive_sha256"]:
        raise ValueError("Archive does not match release.json")
    records = {row["path"]: row for row in metadata["files"]}
    if len(records) != len(metadata["files"]):
        raise ValueError("Duplicate paths in release metadata")
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        if len(members) != len(records) or {m.name for m in members} != set(records):
            raise ValueError("Archive members do not match the release inventory")
        for member in members:
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or ".." in path.parts or "\\" in member.name
                    or path.as_posix() != member.name or member.name == "."):
                raise ValueError(f"Unsafe release member: {member.name}")
            blob = tar.extractfile(member).read()
            row = records[member.name]
            if len(blob) != row["bytes"] or hashlib.sha256(blob).hexdigest() != row["sha256"]:
                raise ValueError(f"Release member hash differs: {member.name}")
        if destination.exists():
            raise ValueError(f"Extraction destination already exists: {destination}")
        destination.mkdir(parents=True)
        for member in members:
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tar.extractfile(member).read())
    return metadata
