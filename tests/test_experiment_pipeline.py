from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from driveloop.experiment_pipeline import (
    ExperimentCase,
    ExperimentPipeline,
    ExperimentPipelineConfig,
    load_experiment_cases,
    perception_evaluator_class,
)
from scripts.run_driveloop_experiment import main


def test_perception_protocol_selects_evaluator_class():
    from driveloop.composite_perception import CompositePerceptionVideoEvaluator
    from driveloop.perception_v10 import (
        ManeuverViewRestrictedSuperclassEvaluator,
        SuperclassCompositePerceptionEvaluator,
    )

    assert perception_evaluator_class("v9") is CompositePerceptionVideoEvaluator
    assert perception_evaluator_class("v10a") is SuperclassCompositePerceptionEvaluator
    assert perception_evaluator_class("v10b") is ManeuverViewRestrictedSuperclassEvaluator
    # default and case-insensitivity
    assert perception_evaluator_class(None) is CompositePerceptionVideoEvaluator
    assert perception_evaluator_class("V10B") is ManeuverViewRestrictedSuperclassEvaluator
    # v10b is the adopted protocol of record; v9 must be requested explicitly
    assert ExperimentPipelineConfig().perception_protocol == "v10b"
    with pytest.raises(ValueError):
        perception_evaluator_class("v11")


def test_experiment_pipeline_writes_case_and_summary_records():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        summary = ExperimentPipeline(
            output_dir=root / "run",
            config=ExperimentPipelineConfig(max_iterations=2, target_score=0.7),
        ).run_cases([
            ExperimentCase(
                name="motorcycle lane change",
                prompt="realistic autonomous driving scene with motorcycle lane change",
                tags=["motorcycle", "lane_change"],
                expected_condition={"actor": "motorcycle"},
            ),
            ExperimentCase(
                name="low visibility vehicle",
                prompt="night autonomous driving scene with low visibility and nearby vehicles",
                tags=["low_visibility"],
            ),
        ])

        summary_json = json.loads((root / "run" / "summary.json").read_text())
        case_json = json.loads((root / "run" / "motorcycle-lane-change" / "case_summary.json").read_text())
        attempts = (root / "run" / "motorcycle-lane-change" / "attempts.jsonl").read_text().splitlines()
        summary_md = (root / "run" / "summary.md").read_text()

    assert summary["schema_version"] == "driveloop_experiment_summary.v0"
    assert summary_json["case_count"] == 2
    assert case_json["claim_boundary"]["semantic_success_requires_measured_passed_alignment_eval"] is True
    assert case_json["claim_boundary"]["mock_backend_is_not_dd2_gpu_evidence"] is True
    assert case_json["claim_boundary"]["semantic_success_claim_allowed"] is False
    assert summary_json["semantic_success_claim_allowed_count"] == 0
    assert attempts
    assert "Claim boundary" in summary_md


def test_load_experiment_cases_accepts_manifest_dict():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = Path(tmpdir) / "cases.json"
        manifest.write_text(json.dumps({
            "cases": [
                {
                    "name": "source bound case",
                    "prompt": "clear road scene",
                    "metadata": {"source_selection": {"requested": True}},
                }
            ]
        }))

        cases = load_experiment_cases(manifest)

    assert cases == [
        ExperimentCase(
            name="source bound case",
            prompt="clear road scene",
            metadata={"source_selection": {"requested": True}},
        )
    ]


def test_experiment_cli_runs_mock_pipeline():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        manifest = root / "cases.json"
        manifest.write_text(json.dumps({
            "cases": [{"name": "cli case", "prompt": "realistic autonomous driving scene"}]
        }))

        assert main([
            "--cases",
            str(manifest),
            "--output-dir",
            str(root / "out"),
            "--max-iterations",
            "1",
        ]) == 0

        summary = json.loads((root / "out" / "summary.json").read_text())

    assert summary["case_count"] == 1
    assert summary["claim_boundary"]["experiment_summary_is_not_video_semantic_success"] is True


def test_experiment_pipeline_builds_drivedreamer2_backend_factory():
    from driveloop.backends import DriveDreamer2Backend

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pipeline = ExperimentPipeline(
            output_dir=root / "run",
            config=ExperimentPipelineConfig(
                backend_name="drivedreamer2",
                dd2_project_root=".",
                dd2_config_name="cfg",
                dd2_baseline_output_dir="baseline_out",
                dd2_baseline_dataset_dir="dataset",
                dd2_audit_only=True,
                dd2_batch_skip=7,
                dd2_source_candidate_id="candidate70",
                dd2_instance_token="instance-token",
                dd2_source_identity_summary="summary.json",
                dd2_timeout_seconds=12,
            ),
        )
        backend = pipeline.backend_factory(root / "artifacts")

    assert isinstance(backend, DriveDreamer2Backend)
    assert backend.config_name == "cfg"
    assert backend.artifact_dir == root / "artifacts"
    assert backend.baseline_output_dir == Path("baseline_out")
    assert backend.baseline_dataset_dir == Path("dataset")
    assert backend.audit_only is True
    assert backend.batch_skip == 7
    assert backend.source_candidate_id == "candidate70"
    assert backend.instance_token == "instance-token"
    assert backend.source_identity_summary_path == Path("summary.json")
    assert backend.timeout_seconds == 12


def test_experiment_pipeline_public_api_exports():
    from driveloop import (
        ExperimentCase as PublicExperimentCase,
        ExperimentPipeline as PublicExperimentPipeline,
        ExperimentPipelineConfig as PublicExperimentPipelineConfig,
        load_experiment_cases as public_load_experiment_cases,
    )

    assert PublicExperimentCase is ExperimentCase
    assert PublicExperimentPipeline is ExperimentPipeline
    assert PublicExperimentPipelineConfig is ExperimentPipelineConfig
    assert public_load_experiment_cases is load_experiment_cases


def test_experiment_pipeline_config_passes_boxes3d_probe_to_dd2_backend():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pipeline = ExperimentPipeline(
            output_dir=root / "run",
            config=ExperimentPipelineConfig(
                backend_name="drivedreamer2",
                dd2_audit_only=True,
                dd2_force_boxes3d_probe=True,
                dd2_boxes3d_probe_category="motorcycle",
            ),
        )
        backend = pipeline.backend_factory(root / "artifacts")

    assert backend.force_boxes3d_probe is True
    assert backend.boxes3d_probe_category == "motorcycle"
