import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from driveloop.experiment_pipeline import ExperimentPipeline, ExperimentPipelineConfig


def test_config_default_frame_num_is_8():
    assert ExperimentPipelineConfig().dd2_frame_num == 8


def test_dd2_backend_factory_receives_frame_num(tmp_path):
    config = ExperimentPipelineConfig(backend_name="drivedreamer2", dd2_frame_num=48)
    pipeline = ExperimentPipeline(output_dir=tmp_path / "out", config=config)
    backend = pipeline.backend_factory(tmp_path / "artifacts")
    assert backend.source_selector_frame_num == 48


def test_cli_exposes_dd2_frame_num():
    source = (REPO_ROOT / "scripts" / "run_driveloop_experiment.py").read_text(encoding="utf-8")
    assert "--dd2-frame-num" in source
    assert "dd2_frame_num=args.dd2_frame_num" in source
