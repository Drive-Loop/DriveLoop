import json
import sys
from pathlib import Path

import lmdb


def _import_lmdb_dataset_module():
    repo_root = Path(__file__).resolve().parents[1]
    path = str(repo_root / 'dreamer-datasets')
    if path not in sys.path:
        sys.path.insert(0, path)
    from dreamer_datasets.datasets import lmdb_dataset

    return lmdb_dataset


lmdb_dataset = _import_lmdb_dataset_module()


class TestLmdbWriterCommitInterval:
    def _write_and_close(self, data_path, count):
        writer = lmdb_dataset.LmdbWriter(data_path)
        for i in range(count):
            writer.write_dict(i, {'value': i})
        writer.write_config()
        writer.close()

    def _entries(self, data_path):
        env = lmdb.open(data_path, readonly=True, lock=False)
        with env.begin() as txn:
            entries = txn.stat()['entries']
        env.close()
        return entries

    def test_all_entries_present_with_small_interval(self, tmp_path, monkeypatch):
        monkeypatch.setenv('DRIVELOOP_LMDB_COMMIT_INTERVAL', '3')
        data_path = str(tmp_path / 'db_small_interval')
        self._write_and_close(data_path, 10)
        assert self._entries(data_path) == 10
        config = json.loads((Path(data_path) / 'config.json').read_text())
        assert config['data_size'] == 10

    def test_default_interval_unchanged_behavior(self, tmp_path, monkeypatch):
        monkeypatch.delenv('DRIVELOOP_LMDB_COMMIT_INTERVAL', raising=False)
        data_path = str(tmp_path / 'db_default_interval')
        self._write_and_close(data_path, 5)
        assert self._entries(data_path) == 5

    def test_interval_boundary_exact_multiple(self, tmp_path, monkeypatch):
        monkeypatch.setenv('DRIVELOOP_LMDB_COMMIT_INTERVAL', '5')
        data_path = str(tmp_path / 'db_boundary')
        self._write_and_close(data_path, 15)
        assert self._entries(data_path) == 15


class TestLmdbWriterImageBytes:
    def test_roundtrip_and_config(self, tmp_path):
        payload_a = b'\x89PNG-fake-a'
        payload_b = b'\x89PNG-fake-b'
        data_path = str(tmp_path / 'db_bytes')
        writer = lmdb_dataset.LmdbWriter(data_path)
        writer.write_image_bytes(3, payload_a)
        writer.write_image_bytes('7', payload_b)
        writer.write_config(data_name='image_hdmap')
        writer.close()

        env = lmdb.open(data_path, readonly=True, lock=False)
        with env.begin() as txn:
            assert txn.get(b'3') == payload_a
            assert txn.get(b'7') == payload_b
            assert txn.stat()['entries'] == 2
        env.close()
        config = json.loads((Path(data_path) / 'config.json').read_text())
        assert config['data_size'] == 2
        assert config['data_name'] == 'image_hdmap'
