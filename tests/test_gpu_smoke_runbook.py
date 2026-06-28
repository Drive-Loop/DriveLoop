from scripts.run_gpu_smoke_runbook import render_runbook


def sample_plan():
    return {
        "scenario_id": "motorcycle_case",
        "prompt": "daytime urban road with a motorcycle changing lane",
        "expected_video_path": "outputs/case/artifacts/motorcycle_case/iteration_00.mp4",
        "commands": {
            "readiness_gate": "python scripts/run_gpu_smoke_readiness_gate.py --output gate.json",
            "gpu_smoke_candidate_generation": "python scripts/run_driveloop_drivedreamer2.py --max-iterations 1",
            "post_gpu_review_gate": "python scripts/run_post_gpu_review_gate.py --video-path video.mp4",
            "alignment_eval_after_completed_review": "python scripts/run_prompt_video_alignment_eval.py --alignment-report report.json",
        },
        "claim_boundary": {
            "gpu_smoke_generates": "candidate_video_only",
            "semantic_claim_allowed_after_gpu": False,
            "lane_change_control_claim_allowed": False,
            "required_before_semantic_claim": "explicit review evidence",
        },
        "notes": [
            "Runtime tensor/hash changes do not prove video semantics or lane-change motion.",
        ],
    }


def test_runbook_contains_full_command_chain():
    runbook = render_runbook(sample_plan())

    assert "scripts/run_gpu_smoke_readiness_gate.py" in runbook
    assert "scripts/run_driveloop_drivedreamer2.py" in runbook
    assert "scripts/run_post_gpu_review_gate.py" in runbook
    assert "scripts/run_prompt_video_alignment_eval.py" in runbook


def test_runbook_preserves_claim_boundary():
    runbook = render_runbook(sample_plan())

    assert "candidate_video_only" in runbook
    assert "Semantic success allowed after GPU alone: `False`" in runbook
    assert "Lane-change control claim allowed: `False`" in runbook
    assert "Do not claim prompt-to-video semantic success" in runbook
    assert "record `measured_failed`" in runbook
