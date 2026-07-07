import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from driveloop.tau_reanchoring import (
    SCHEMA_VERSION,
    acceptance_at,
    build_tau_reanchoring,
    candidate_taus,
    load_arm,
    percentile,
    render_markdown,
    summarize,
)

OPEN_BEST_J = [0.4, 0.45, 0.5, 0.55, 0.6]
CLOSED_BEST_J = [0.5, 0.55, 0.6, 0.62, 0.63]


def write_arm(root: Path, name: str, best_js, use_best_metrics: bool = True) -> Path:
    arm_dir = root / name
    cases = []
    for i, best in enumerate(best_js):
        case_name = f"m{i + 1}_case"
        case = {"name": case_name, "status": "failed", "best_score": best}
        if use_best_metrics:
            case["best_metrics"] = {"J": best, "S_perc": 0.3}
        cases.append(case)
        case_dir = arm_dir / case_name
        case_dir.mkdir(parents=True)
        rows = [
            {"evaluation": {"score": best - 0.1, "metrics": {"J": best - 0.1}}},
            {"evaluation": {"score": best, "metrics": {"J": best}}},
        ]
        with (case_dir / "attempts.jsonl").open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
    summary = {"accepted_count": 0, "cases": cases}
    (arm_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return arm_dir


def test_percentile_interpolation():
    values = [0.4, 0.45, 0.5, 0.55, 0.6]
    assert percentile(values, 50.0) == pytest.approx(0.5)
    assert percentile(values, 75.0) == pytest.approx(0.55)
    assert percentile(values, 90.0) == pytest.approx(0.58)
    assert percentile(values, 0.0) == pytest.approx(0.4)
    assert percentile(values, 100.0) == pytest.approx(0.6)


def test_summarize_sample_std():
    stats = summarize(OPEN_BEST_J)
    assert stats["count"] == 5
    assert stats["mean"] == pytest.approx(0.5)
    expected_std = math.sqrt(sum((v - 0.5) ** 2 for v in OPEN_BEST_J) / 4)
    assert stats["std"] == pytest.approx(expected_std, abs=1e-6)
    assert summarize([0.5])["std"] is None
    assert summarize([])["mean"] is None


def test_load_arm_reads_best_and_attempt_j(tmp_path):
    arm = load_arm("open_loop", write_arm(tmp_path, "open_loop", OPEN_BEST_J))
    assert arm.best_j == pytest.approx(OPEN_BEST_J)
    assert len(arm.attempt_j) == 2 * len(OPEN_BEST_J)
    assert arm.accepted_count_recorded == 0
    assert len(arm.case_names) == len(OPEN_BEST_J)


def test_load_arm_falls_back_to_best_score(tmp_path):
    arm_dir = write_arm(tmp_path, "open_loop", OPEN_BEST_J, use_best_metrics=False)
    assert load_arm("open_loop", arm_dir).best_j == pytest.approx(OPEN_BEST_J)


def test_load_arm_missing_summary_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_arm("open_loop", tmp_path / "does_not_exist")


def test_candidate_taus_rules():
    candidates = candidate_taus(OPEN_BEST_J)
    std = math.sqrt(sum((v - 0.5) ** 2 for v in OPEN_BEST_J) / 4)
    assert candidates["anchor_mean_plus_1_std"] == pytest.approx(0.5 + std, abs=1e-6)
    assert candidates["anchor_mean_plus_0p5_std"] == pytest.approx(0.5 + 0.5 * std, abs=1e-6)
    assert candidates["anchor_p75"] == pytest.approx(0.55)
    assert candidates["anchor_p90"] == pytest.approx(0.58)


def test_acceptance_at_threshold(tmp_path):
    arm = load_arm("closed_loop", write_arm(tmp_path, "closed_loop", CLOSED_BEST_J))
    result = acceptance_at(arm, 0.6)
    assert result["accepted_count"] == 3
    assert result["case_count"] == 5
    assert acceptance_at(arm, 0.7)["accepted_count"] == 0


def test_build_manifest_end_to_end(tmp_path):
    manifest = build_tau_reanchoring(
        arm_dirs={
            "open_loop": write_arm(tmp_path, "open_loop", OPEN_BEST_J),
            "closed_loop": write_arm(tmp_path, "closed_loop", CLOSED_BEST_J),
        },
        anchor_arm="open_loop",
        current_tau=0.7,
        capability_configuration="unit_test_config",
    )
    assert manifest["schema_version"] == SCHEMA_VERSION
    std = math.sqrt(sum((v - 0.5) ** 2 for v in OPEN_BEST_J) / 4)
    assert manifest["proposed_tau"] == pytest.approx(0.5 + std, abs=1e-6)
    assert manifest["proposed_tau_grid_0p05"] == pytest.approx(0.6)

    current = manifest["acceptance_table"]["current_tau"]
    assert current["per_arm"]["open_loop"]["accepted_count"] == 0
    assert current["per_arm"]["closed_loop"]["accepted_count"] == 0
    proposed = manifest["acceptance_table"]["anchor_mean_plus_1_std"]
    assert proposed["per_arm"]["open_loop"]["accepted_count"] == 1
    assert proposed["per_arm"]["closed_loop"]["accepted_count"] == 3

    boundary = manifest["claim_boundary"]
    assert boundary["tau_reanchoring_is_not_video_semantic_success"] is True
    assert boundary["anchor_arm_is_open_loop_baseline"] is True
    assert boundary["comparison_requires_fresh_runs_at_frozen_tau"] is True
    assert boundary["small_anchor_sample_caveat"] is True
    assert boundary["anchor_case_count"] == 5

    markdown = render_markdown(manifest)
    assert "anchor_mean_plus_1_std" in markdown
    assert "3/5" in markdown


def test_build_manifest_missing_anchor_raises(tmp_path):
    with pytest.raises(ValueError, match="anchor arm"):
        build_tau_reanchoring(
            arm_dirs={"open_loop": write_arm(tmp_path, "open_loop", OPEN_BEST_J)},
            anchor_arm="closed_loop",
            current_tau=0.7,
        )


def test_build_manifest_unknown_rule_raises(tmp_path):
    with pytest.raises(ValueError, match="primary rule"):
        build_tau_reanchoring(
            arm_dirs={"open_loop": write_arm(tmp_path, "open_loop", OPEN_BEST_J)},
            anchor_arm="open_loop",
            current_tau=0.7,
            primary_rule="not_a_rule",
        )


def test_script_main_writes_outputs(tmp_path):
    open_dir = write_arm(tmp_path, "open_loop", OPEN_BEST_J)
    closed_dir = write_arm(tmp_path, "closed_loop", CLOSED_BEST_J)
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        import run_tau_reanchoring_analysis as script
    finally:
        sys.path.pop(0)
    json_out = tmp_path / "tau.json"
    md_out = tmp_path / "tau.md"
    code = script.main(
        [
            "--arm", f"open_loop={open_dir}",
            "--arm", f"closed_loop={closed_dir}",
            "--anchor-arm", "open_loop",
            "--current-tau", "0.7",
            "--capability-configuration", "unit_test_config",
            "--output", str(json_out),
            "--markdown-output", str(md_out),
        ]
    )
    assert code == 0
    manifest = json.loads(json_out.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["capability_configuration"] == "unit_test_config"
    assert md_out.read_text(encoding="utf-8").startswith("# Tau re-anchoring analysis")
