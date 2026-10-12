#!/usr/bin/env python3
"""Exercise rejection of damaged and unsafe release archives."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from release_support import extract_release


class ReleaseSafety(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.release = self.root / "release"
        self.release.mkdir()
        self.destination = self.root / "site"

    def fixture(self, name="index.html", kind=tarfile.REGTYPE, expected_hash=None):
        blob = b"a known, independent fixture\n"
        archive = self.release / "site.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            member = tarfile.TarInfo(name)
            member.type = kind
            if kind == tarfile.SYMTYPE:
                member.linkname = "../outside.html"
                tar.addfile(member)
            else:
                member.size = len(blob)
                tar.addfile(member, io.BytesIO(blob))
        metadata = {"archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                    "files": [{"path": name, "bytes": len(blob),
                               "sha256": expected_hash or hashlib.sha256(blob).hexdigest()}]}
        (self.release / "release.json").write_text(json.dumps(metadata))
        return blob

    def rejected(self):
        with self.assertRaises(ValueError):
            extract_release(self.release, self.destination)
        self.assertFalse(self.destination.exists())
        self.assertFalse((self.root / "outside.html").exists())

    def test_valid_archive(self):
        blob = self.fixture()
        extract_release(self.release, self.destination)
        self.assertEqual((self.destination / "index.html").read_bytes(), blob)

    def test_archive_hash_tampering(self):
        self.fixture()
        with (self.release / "site.tar.gz").open("ab") as archive:
            archive.write(b"unexpected content")
        self.rejected()

    def test_member_hash_tampering(self):
        self.fixture(expected_hash="0" * 64)
        self.rejected()

    def test_parent_traversal(self):
        self.fixture(name="../outside.html")
        self.rejected()

    def test_symlink_member(self):
        self.fixture(kind=tarfile.SYMTYPE)
        self.rejected()

    def test_ambiguous_member_path(self):
        self.fixture(name="./index.html")
        self.rejected()


if __name__ == "__main__":
    unittest.main()
