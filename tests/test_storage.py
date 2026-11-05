import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.storage import write_json


class CheckpointTests(unittest.TestCase):
    def test_creates_parent_and_replaces_existing_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nested' / 'run.json'
            write_json(path, {'status': 'pending'})
            write_json(path, {'status': 'done', 'label': 'café'})
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')),
                             {'status': 'done', 'label': 'café'})
            self.assertFalse(path.with_suffix('.json.tmp').exists())

    def test_serialization_failure_preserves_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'run.json'
            write_json(path, {'status': 'pending'})
            previous = path.read_bytes()
            with self.assertRaises(TypeError):
                write_json(path, {'invalid': object()})
            self.assertEqual(previous, path.read_bytes())

    def test_replace_failure_preserves_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'run.json'
            write_json(path, {'status': 'pending'})
            previous = path.read_bytes()
            with patch.object(Path, 'replace', side_effect=OSError('locked')):
                with self.assertRaises(OSError):
                    write_json(path, {'status': 'done'})
            self.assertEqual(previous, path.read_bytes())


if __name__ == '__main__':
    unittest.main()
