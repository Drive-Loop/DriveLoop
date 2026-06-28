import json
from pathlib import Path

from scripts.run_dd2_runtime_hash_compare import build_compare


def write_summary(path: Path, prompt_hash: str, box_hash: str, grounding_hash: str, img_hash: str):
    path.write_text(
        json.dumps(
            {
                "prompt": "test prompt",
                "runtime_input_audit": {
                    "prompt_override": "test prompt.",
                    "prompt_embed": {"sha256": prompt_hash, "available": True},
                    "box_downsampler_input": {"sha256": box_hash, "available": True},
                    "grounding_downsampler_input": {"sha256": grounding_hash, "available": True},
                    "img_cond": {"sha256": img_hash, "available": True},
                },
                "override_audit": {
                    "changed_counts": {
                        "boxes3d": 48,
                        "image_box": 48,
                        "scene_description": 48,
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_runtime_hash_compare_marks_changed_and_unchanged_tensors(tmp_path: Path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    write_summary(a, "prompt_a", "same_box", "same_grounding", "same_img")
    write_summary(b, "prompt_b", "same_box", "same_grounding", "same_img")

    report = build_compare(a, b, "earlier", "refined")

    assert report["runtime_tensor_hash_changed"]["prompt_embed"] is True
    assert report["runtime_tensor_hash_changed"]["box_downsampler_input"] is False
    assert report["runtime_tensor_hash_changed"]["grounding_downsampler_input"] is False
    assert report["runtime_tensor_hash_changed"]["img_cond"] is False
    assert report["interpretation"]["text_condition_changed"] is True
    assert report["interpretation"]["box_structural_condition_changed"] is False
    assert "does not prove generated video semantics" in report["interpretation"]["claim_boundary"]
