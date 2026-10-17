#!/usr/bin/env python3
"""Independent safety regressions for fixed installer arguments, retention and capacity."""
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'deploy/scripts'))
from retention import capacity, retention_plan, stale_temporaries
from publish_release import immutable_owner


class PolicyTests(unittest.TestCase):
    def test_web_tmpfiles_requires_only_web_host_accounts(self):
        rows=[line.split() for line in (ROOT/'deploy/systemd/reading-notes.tmpfiles.conf').read_text().splitlines() if line and not line.startswith('#')]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row[3],{'root','reading-notes'})
            self.assertIn(row[4],{'root','reading-notes'})
            self.assertFalse(row[1].startswith('/var/lock/'))

    def test_installed_permissions_check_owner_and_write_bits(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'release';path.mkdir();file=path/'data';file.write_text('immutable')
            try:
                with self.assertRaises(ValueError):immutable_owner(path,expected_uid=os.getuid())
                file.chmod(0o444);path.chmod(0o555)
                immutable_owner(path,expected_uid=os.getuid())
                with self.assertRaises(ValueError):immutable_owner(path,expected_uid=os.getuid()+1)
            finally:path.chmod(0o755);file.chmod(0o644)

    def test_installer_accepts_no_arbitrary_path_command_or_test_hook(self):
        arguments=runpy.run_path(str(ROOT/'deploy/scripts/reading-notes-publish'))['arguments']
        for args in [['publish','../../tmp/x'],['publish','20990101T000001','--service-hook','/tmp/x'],['recover','--root','/tmp/x'],['sh','-c','id'],[]]:
            with self.assertRaises(ValueError):arguments(args)
        self.assertEqual(arguments(['publish','20990101T000001']),['--release-dir','/var/spool/reading-notes/ready/20990101T000001'])

    def test_bytes_and_inode_guards_are_independent(self):
        for free,inodes in [(1024,100000),(10**10,2)]:
            with patch('retention.os.statvfs',return_value=SimpleNamespace(f_bavail=free,f_frsize=1,f_favail=inodes)):
                with self.assertRaisesRegex(ValueError,'headroom'):capacity('/',1000,20)

    def test_retention_keeps_current_previous_transaction_and_recent_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'releases').mkdir()
            for i in range(1,7):
                p=root/f'releases/20990101T00000{i}';p.mkdir();os.utime(p,(0,0))
            (root/'current').symlink_to('releases/20990101T000001')
            (root/'.last-publish.json').write_text(json.dumps({'previous':'releases/20990101T000002','current':'releases/20990101T000001'}))
            (root/'.publish-transaction.json').write_text(json.dumps({'previous':'releases/20990101T000003','candidate':'releases/20990101T000004'}))
            self.assertEqual(retention_plan(root,2),[])
            (root/'.publish-transaction.json').unlink()
            self.assertEqual([p.name for p in retention_plan(root,2)],['20990101T000004','20990101T000003'])
            with self.assertRaises(ValueError):retention_plan(root,1)

    def test_only_stale_known_temporary_names_are_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'releases').mkdir()
            old=root/'.unpack-old123';old.mkdir();(old/'data').write_text('partial');os.utime(old,(0,0))
            recent=root/'.unpack-recent';recent.mkdir()
            unrelated=root/'.unpack-not-eligible.txt';unrelated.write_text('retain')
            (root/'.publish-transaction.json').write_text('{}')
            self.assertEqual(stale_temporaries(root),[])
            (root/'.publish-transaction.json').unlink()
            self.assertEqual(stale_temporaries(root),['.unpack-old123'])
            self.assertTrue(recent.exists() and unrelated.exists())

    def test_queue_symlink_cannot_redirect_root_snapshot(self):
        namespace=runpy.run_path(str(ROOT/'deploy/scripts/reading-notes-publish'))
        snapshot=namespace['snapshot']
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);queue=root/'queue';queue.mkdir();dest=root/'destination';dest.mkdir()
            source=queue/'20990101T000001';source.mkdir();(source/'release.json').symlink_to('/etc/passwd')
            with patch.dict(snapshot.__globals__,{'QUEUE':queue}):
                with self.assertRaises(OSError):snapshot(source,dest)
            self.assertEqual(list(dest.iterdir()),[])


if __name__=='__main__':unittest.main()
