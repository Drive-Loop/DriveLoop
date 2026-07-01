from pathlib import Path


def test_transform_preserves_motion_metadata_audit_only():
    text = Path("dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_transforms.py").read_text(
        encoding="utf-8"
    )

    assert "'motion_metadata': motion_metadata" in text
    assert "'velocities_available_in_batch': velocities is not None" in text
    assert "'actor_identity_available_in_batch': bool(actor_identity_fields)" in text
    assert "'actor_identity_fields': actor_identity_fields" in text
    assert "'per_frame_actor_boxes3d_observed': False" in text
    assert "'claim': 'metadata_observed_only_not_runtime_control'" in text


def test_tester_writes_motion_metadata_to_runtime_audit_only():
    text = Path("dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_tester.py").read_text(
        encoding="utf-8"
    )

    assert "motion_metadata = batch_dict.get('motion_metadata', None)" in text
    assert '"motion_metadata": metadata_summary(motion_metadata)' in text
    assert '"velocities_available_in_batch_any": bool_any(raw_velocities_available)' in text
    assert '"velocities_shape_preview": shape_preview(value.get("velocities_shape"))' in text
    assert '"boxes3d_shape_preview": shape_preview(value.get("boxes3d_shape"))' in text
    assert '"actor_identity_available_in_batch_any": bool_any(raw_actor_identity)' in text
    assert '"per_frame_actor_boxes3d_observed_any": bool_any(raw_per_frame_boxes)' in text
    assert '"metadata_observed_only_not_runtime_control"' in text


def test_motion_metadata_shape_preview_handles_collated_shapes():
    source = Path("dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_tester.py").read_text(encoding="utf-8")
    assert "looks_transposed = 1 < len(normalized) <= 4" in source
    assert "zip(*normalized)" in source
    assert "metadata_observed_only_not_runtime_control" in source
