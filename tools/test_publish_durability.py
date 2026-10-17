#!/usr/bin/env python3
"""Durability ordering and failed-write regressions; no claim of physical power loss."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'deploy/scripts'))
import durability


class DurabilityTests(unittest.TestCase):
    def test_failed_file_flush_keeps_old_journal(self):
        with tempfile.TemporaryDirectory() as temp:
            journal = Path(temp)/'journal.json'
            journal.write_text('{"previous":"old"}')
            with patch.object(durability.os, 'fsync', side_effect=OSError('power-cut model')):
                with self.assertRaises(OSError):
                    durability.atomic_json(journal, {'previous': 'new'})
            self.assertEqual(json.loads(journal.read_text()), {'previous': 'old'})

    def test_atomic_replace_flushes_parent_and_never_truncates_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            journal = Path(temp)/'journal.json'
            journal.write_text('{"previous":"old"}')
            events = []
            replace = os.replace
            def replacing(source, target):
                self.assertEqual(json.loads(journal.read_text()), {'previous': 'old'})
                self.assertEqual(json.loads(Path(source).read_text()), {'previous': 'new'})
                events.append('replace')
                replace(source, target)
            with patch.object(durability.os, 'replace', side_effect=replacing), patch.object(durability.os, 'fsync', side_effect=lambda fd: events.append('fsync')):
                durability.atomic_json(journal, {'previous': 'new'})
            self.assertEqual(events, ['fsync', 'replace', 'fsync'])

    def test_tree_files_precede_directories_and_parents(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'site').mkdir()
            (root/'site/index.html').write_text('complete payload')
            (root/'release.json').write_text('{}')
            events = []
            with patch.object(durability, 'sync_file', side_effect=lambda p: events.append(('file', p.relative_to(root).as_posix()))), patch.object(durability, 'sync_directory', side_effect=lambda p: events.append(('directory', p.relative_to(root).as_posix()))):
                durability.sync_tree(root)
            self.assertEqual({x[1] for x in events[:2]}, {'site/index.html', 'release.json'})
            self.assertEqual(events[2:], [('directory', 'site'), ('directory', '.')])

    def test_tree_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'bad').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):
                durability.sync_tree(root)

    def test_queue_flushes_tree_then_rename_then_parent(self):
        spec = importlib.util.spec_from_file_location('queue_release', ROOT/'deploy/scripts/queue-release.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); builder=root/'builder'; queue=root/'queue'
            builder.mkdir(); queue.mkdir()
            source=builder/'20990101T000001'; source.mkdir(); (source/'data').write_text('complete')
            events=[]; rename=os.rename
            def renaming(source, target):
                events.append('rename'); rename(source,target)
            with patch.object(module, 'sync_tree', side_effect=lambda p: events.append('tree')), patch.object(module.os, 'rename', side_effect=renaming), patch.object(module, 'sync_directory', side_effect=lambda p: events.append('parent')):
                module.queue_release(source, queue, builder)
            self.assertEqual(events, ['tree', 'rename', 'parent'])


if __name__ == '__main__':
    unittest.main()
