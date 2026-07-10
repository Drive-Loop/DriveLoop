import sys
from pathlib import Path

import pytest
import torch
import torch.nn as nn


def _import_trainer_module():
    repo_root = Path(__file__).resolve().parents[1]
    # Mirror ENV.init_paths: the dreamer-* packages are path-injected, not pip-installed.
    for rel in (
        'dreamer-datasets',
        'dreamer-models',
        'dreamer-train',
        'dreamer-train/projects/DriveDreamer2',
    ):
        path = str(repo_root / rel)
        if path not in sys.path:
            sys.path.insert(0, path)
    from drivedreamer2 import drivedreamer2_trainer

    return drivedreamer2_trainer


trainer_mod = _import_trainer_module()


class TestEdmParameterizationMatchesInference:
    def test_denoised_matches_euler_v_prediction_formula(self):
        torch.manual_seed(0)
        for sigma_value in (0.05, 0.5, 2.0, 40.0, 300.0):
            sigma = torch.tensor([sigma_value], dtype=torch.float64)
            x_t = torch.randn(2, 3, 4, dtype=torch.float64)
            model_output = torch.randn(2, 3, 4, dtype=torch.float64)

            c_in, c_skip, c_out, c_noise = trainer_mod.edm_scalings(sigma)

            # scale_model_input in EulerDiscreteScheduler: sample / sqrt(sigma^2 + 1)
            assert torch.allclose(x_t * c_in, x_t / (sigma**2 + 1) ** 0.5)

            # step() with prediction_type='v_prediction':
            # denoised = model_output * (-sigma / sqrt(sigma^2 + 1)) + sample / (sigma^2 + 1)
            reference = model_output * (-sigma / (sigma**2 + 1) ** 0.5) + x_t / (sigma**2 + 1)
            mine = model_output * c_out + x_t * c_skip
            assert torch.allclose(mine, reference)

            # timestep_type='continuous': t = 0.25 * log(sigma)
            assert torch.allclose(c_noise, 0.25 * torch.log(sigma))

    def test_loss_weight_finite_and_positive(self):
        sigmas = torch.exp(torch.linspace(-6, 6, 50, dtype=torch.float64))
        weights = trainer_mod.edm_loss_weight(sigmas)
        assert torch.isfinite(weights).all()
        assert (weights > 0).all()


class TestPanoramicReshape:
    def test_matches_naive_loop(self):
        cam_num, frame_num, channels, height, width = 3, 2, 2, 4, 5
        records = torch.arange(
            cam_num * frame_num * channels * height * width, dtype=torch.float32
        ).reshape(cam_num * frame_num, channels, height, width)

        result = trainer_mod.panoramic_from_records(records, cam_num, frame_num)
        assert result.shape == (frame_num, channels, height, width * cam_num)

        for frame in range(frame_num):
            for cam in range(cam_num):
                record = records[cam * frame_num + frame]
                segment = result[frame, :, :, cam * width : (cam + 1) * width]
                assert torch.equal(segment, record)

    def test_rejects_wrong_leading_dim(self):
        with pytest.raises(ValueError):
            trainer_mod.panoramic_from_records(torch.zeros(5, 1, 2, 2), cam_num=3, frame_num=2)


class TestTrainableSelection:
    def _named_params(self):
        module = nn.Module()
        module.spatial = nn.Linear(2, 2)
        module.temporal_transformer_blocks = nn.ModuleList([nn.Linear(2, 2)])
        module.time_mixer = nn.Linear(2, 2)
        return list(module.named_parameters())

    def test_default_patterns_select_temporal_only(self, monkeypatch):
        monkeypatch.delenv('DRIVELOOP_FT_TRAIN_PATTERNS', raising=False)
        patterns = trainer_mod.resolve_train_patterns()
        selected = trainer_mod.select_trainable_param_names(self._named_params(), patterns)
        assert any('temporal_transformer_blocks' in name for name in selected)
        assert any('time_mixer' in name for name in selected)
        assert not any(name.startswith('spatial') for name in selected)

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv('DRIVELOOP_FT_TRAIN_PATTERNS', 'spatial')
        patterns = trainer_mod.resolve_train_patterns()
        selected = trainer_mod.select_trainable_param_names(self._named_params(), patterns)
        assert all(name.startswith('spatial') for name in selected)
        assert len(selected) == 2

    def test_empty_pattern_list_rejected(self, monkeypatch):
        monkeypatch.setenv('DRIVELOOP_FT_TRAIN_PATTERNS', ' , ')
        with pytest.raises(ValueError):
            trainer_mod.resolve_train_patterns()


class TestGligenExportFormat:
    def test_prefixes_and_meta_isolation(self):
        unet_sd = {'conv_in.weight': torch.zeros(1)}
        gd_sd = {'layers.0.weight': torch.ones(1)}
        bd_sd = {'layers.0.weight': torch.full((1,), 2.0)}
        meta = {
            'unet': {'_class_name': 'UNetSpatioTemporalConditionModel', 'in_channels': 8},
            'grounding_downsampler': {'_class_name': 'GroundingDownSampler', 'out_dim': 8},
            'box_downsampler': {'_class_name': 'GroundingDownSampler', 'out_dim': 20},
        }

        state = trainer_mod.build_gligen_state_dict(unet_sd, gd_sd, bd_sd, meta)

        assert set(state.keys()) == {
            'unet.conv_in.weight',
            'grounding_downsampler.layers.0.weight',
            'box_downsampler.layers.0.weight',
            'meta',
        }
        # load_weights pops '_class_name'; exported meta must still carry it.
        assert state['meta']['unet']['_class_name'] == 'UNetSpatioTemporalConditionModel'

        # meta must be deep-copied: mutating the source must not leak into the export.
        meta['unet']['_class_name'] = 'Mutated'
        assert state['meta']['unet']['_class_name'] == 'UNetSpatioTemporalConditionModel'
