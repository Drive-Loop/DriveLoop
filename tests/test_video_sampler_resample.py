import logging
import sys
from pathlib import Path


def _import_utils_module():
    repo_root = Path(__file__).resolve().parents[1]
    for rel in (
        'dreamer-datasets',
        'dreamer-models',
        'dreamer-train',
        'dreamer-train/projects/DriveDreamer2',
    ):
        path = str(repo_root / rel)
        if path not in sys.path:
            sys.path.insert(0, path)
    from drivedreamer2 import drivedreamer2_utils

    return drivedreamer2_utils


utils_mod = _import_utils_module()


class CountingTransform:
    def __init__(self):
        self.calls = 0

    def __call__(self, data_dict):
        self.calls += 1
        return data_dict


class FakeVideoDataset:
    """Minimal dataset with the raw metadata keys the resample loop consumes."""

    def __init__(self, video_length=10, poisoned=False):
        self.transform = None
        self.records = []
        for frame_idx in range(video_length):
            self.records.append(
                {
                    'frame_idx': frame_idx if not poisoned else 0,
                    'cam_type': 'cam_front',
                    'video_length': video_length,
                }
            )

    def set_transform(self, transform):
        self.transform = transform

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        record = dict(self.records[index])
        if self.transform is not None:
            record = self.transform(record)
        return record


def _build_sampler(dataset, monkeypatch, raw_mode, cache_dir=''):
    monkeypatch.setenv('DRIVELOOP_SAMPLER_RAW_RESAMPLE', '1' if raw_mode else '0')
    if cache_dir:
        monkeypatch.setenv('DRIVELOOP_SAMPLER_CACHE_DIR', cache_dir)
    else:
        monkeypatch.delenv('DRIVELOOP_SAMPLER_CACHE_DIR', raising=False)
    return utils_mod.VideoSampler(
        dataset,
        batch_size=2,
        cam_num=1,
        frame_num=2,
        hz_factor=1,
        video_split_rate=1,
        mv_video=False,
        view='cam_front',
        shuffle=False,
        infinite=False,
        logger=logging.getLogger('test_video_sampler'),
        resample_num_workers=0,
        resample_batch_size=4,
    )


class TestRawResampleEquivalence:
    def test_index_and_total_size_match_transform_path(self, monkeypatch):
        transform_a = CountingTransform()
        dataset_a = FakeVideoDataset()
        dataset_a.set_transform(transform_a)
        sampler_transform = _build_sampler(dataset_a, monkeypatch, raw_mode=False)
        assert transform_a.calls > 0

        transform_b = CountingTransform()
        dataset_b = FakeVideoDataset()
        dataset_b.set_transform(transform_b)
        sampler_raw = _build_sampler(dataset_b, monkeypatch, raw_mode=True)
        assert transform_b.calls == 0, 'raw resample must not invoke the transform'

        assert sampler_raw.index == sampler_transform.index
        assert sampler_raw.total_size == sampler_transform.total_size

    def test_transform_restored_after_raw_resample(self, monkeypatch):
        transform = CountingTransform()
        dataset = FakeVideoDataset()
        dataset.set_transform(transform)
        _build_sampler(dataset, monkeypatch, raw_mode=True)
        assert dataset.transform is transform


class TestSamplerCache:
    def test_cache_roundtrip(self, tmp_path, monkeypatch):
        dataset = FakeVideoDataset()
        sampler_first = _build_sampler(dataset, monkeypatch, raw_mode=True, cache_dir=str(tmp_path))
        cache_files = list(tmp_path.glob('video_sampler_*.pkl'))
        assert len(cache_files) == 1

        # Same length but poisoned records: a cache hit must ignore record contents.
        poisoned = FakeVideoDataset(poisoned=True)
        sampler_cached = _build_sampler(poisoned, monkeypatch, raw_mode=True, cache_dir=str(tmp_path))
        assert sampler_cached.index == sampler_first.index
        assert sampler_cached.total_size == sampler_first.total_size
