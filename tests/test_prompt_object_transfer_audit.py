from scripts.run_prompt_object_transfer_audit import build_audit


def summary_with(category="motorcycle"):
    return {
        "dd2_executable_condition": {
            "actor_controls": [{"category": category}],
            "structural_input_plan": {
                "labels": {"values": [category]},
            },
        },
        "runtime_input_audit": {
            "box_downsampler_input": {"available": True},
        },
        "override_audit": {
            "entries_preview": [
                {
                    "applied": [
                        {
                            "accepted_entries": [
                                {"category": category},
                            ]
                        }
                    ]
                }
            ]
        },
    }


def test_object_transfer_visible_to_override_but_runtime_class_not_decoded():
    audit = build_audit(
        "daytime road with a motorcycle changing lane",
        summary_with("motorcycle"),
    )

    assert audit["requested_objects"] == ["motorcycle"]
    assert audit["status"] == "partially_verified"
    assert audit["checks"]["executable_actor_controls"]["missing_requested_objects"] == []
    assert audit["checks"]["structural_input_plan_labels"]["missing_requested_objects"] == []
    assert audit["checks"]["override_appended_boxes"]["missing_requested_objects"] == []
    assert audit["checks"]["runtime_tensor_class_labels"]["class_label_observable"] is False
    assert audit["blockers"] == ["runtime_tensor_class_label_not_directly_observable"]


def test_blocks_when_requested_object_missing_from_override():
    summary = summary_with("car")
    audit = build_audit(
        "daytime road with a motorcycle changing lane",
        summary,
    )

    assert audit["status"] == "blocked"
    assert "motorcycle" in audit["checks"]["executable_actor_controls"]["missing_requested_objects"]
    assert "motorcycle" in audit["checks"]["override_appended_boxes"]["missing_requested_objects"]


def test_generic_prompt_object_not_motorcycle_specific():
    audit = build_audit(
        "urban road with a pedestrian crossing",
        summary_with("pedestrian"),
    )

    assert audit["requested_objects"] == ["pedestrian"]
    assert audit["status"] == "partially_verified"
    assert audit["checks"]["override_appended_boxes"]["observed_categories"] == ["pedestrian"]


def test_not_applicable_without_known_object_request():
    audit = build_audit(
        "daytime urban road",
        summary_with("motorcycle"),
    )

    assert audit["status"] == "not_applicable"
    assert audit["requested_objects"] == []


def test_uses_paper_alignment_report_when_summary_is_trimmed():
    trimmed_summary = {
        "runtime_input_audit": {
            "box_downsampler_input": {"available": True},
        },
        "override_audit": {
            "entries_preview": [
                {
                    "applied": [
                        {
                            "accepted_entries": [
                                {"category": "motorcycle"},
                            ]
                        }
                    ]
                }
            ]
        },
    }
    paper_report = {
        "stage_1_multimodal_prompt_grounding": {
            "actor_controls": [{"category": "motorcycle"}],
        },
        "stage_3_scene_consistent_generation": {
            "structural_input_plan": {
                "labels": {"values": ["motorcycle"]},
            }
        },
    }

    audit = build_audit(
        "daytime road with a motorcycle changing lane",
        trimmed_summary,
        paper_alignment_report=paper_report,
    )

    assert audit["status"] == "partially_verified"
    assert audit["checks"]["executable_actor_controls"]["observed_categories"] == ["motorcycle"]
    assert audit["checks"]["structural_input_plan_labels"]["observed_labels"] == ["motorcycle"]
    assert audit["checks"]["override_appended_boxes"]["observed_categories"] == ["motorcycle"]
