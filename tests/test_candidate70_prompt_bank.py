import json

from scripts.run_candidate70_prompt_bank import (
    audit_prompt_bank,
    build_candidate70_prompt_bank,
    write_outputs,
)


def test_candidate70_prompt_bank_preserves_claim_boundary():
    bank = build_candidate70_prompt_bank()

    assert bank["schema_version"] == "driveloop_prompt_bank.v0"
    assert bank["does_not_run_gpu"] is True
    assert bank["does_not_generate_video"] is True
    assert bank["prompt_policy"]["accepted_prompt_required_before_generate"] is True
    assert bank["prompt_policy"]["semantic_success_claim_allowed"] is False
    assert sum(1 for item in bank["prompts"] if item["accepted_for_generate"]) == 0


def test_candidate70_prompt_bank_support_audit_counts():
    audit = audit_prompt_bank(build_candidate70_prompt_bank())

    assert audit["schema_version"] == "driveloop_prompt_bank_candidate_support_audit.v0"
    assert audit["does_not_run_gpu"] is True
    assert audit["does_not_generate_video"] is True
    assert audit["accepted_for_generate_count"] == 0
    assert audit["candidate70_allowed_count"] == 4
    assert audit["candidate70_blocked_count"] == 4
    assert audit["claim_boundary"]["prompt_bank_audit_is_not_video_semantic_success"] is True


def test_candidate70_prompt_bank_support_audit_ids_and_blockers():
    audit = audit_prompt_bank(build_candidate70_prompt_bank())
    allowed_ids = {r["id"] for r in audit["results"] if r["allowed_for_candidate70"]}
    blocked = {r["id"]: r["blocked_reasons"] for r in audit["results"] if not r["allowed_for_candidate70"]}

    assert allowed_ids == {"c70_pos_001", "c70_pos_002", "c70_pos_003", "c70_holdout_001"}
    assert blocked["c70_neighbor_001"] == ["candidate70_target_is_motorcycle_not_bicycle"]
    assert blocked["c70_neighbor_002"] == ["candidate70_target_is_motorcycle_not_car"]
    assert blocked["c70_neg_001"] == ["candidate70_is_night_not_daytime"]
    assert blocked["c70_neg_002"] == ["prompt_requests_no_motorcycle_or_scooter"]


def test_candidate70_prompt_bank_writes_outputs(tmp_path):
    bank_path = tmp_path / "candidate70_prompt_bank_v0.json"
    audit_path = tmp_path / "candidate70_prompt_bank_support_audit_v0.json"

    summary = write_outputs(bank_path, audit_path)
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert summary["prompt_count"] == 8
    assert bank["schema_version"] == "driveloop_prompt_bank.v0"
    assert audit["candidate70_allowed_count"] == 4
    assert audit["candidate70_blocked_count"] == 4
    assert audit["bank_path"] == str(bank_path)
