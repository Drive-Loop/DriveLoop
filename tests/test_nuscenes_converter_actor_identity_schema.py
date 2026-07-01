from pathlib import Path


def test_cam_label_converter_preserves_actor_identity_schema():
    text = Path("dreamer-datasets/dd_scripts/converters/nuscenes_converter.py").read_text(encoding="utf-8")

    assert "sample_annotation_tokens = []" in text
    assert "instance_tokens = []" in text
    assert "sample_annotation = self.nusc.get('sample_annotation', cam_box.token)" in text
    assert "sample_annotation_tokens.append(cam_box.token)" in text
    assert "instance_tokens.append(sample_annotation.get('instance_token'))" in text
    assert "'sample_annotation_tokens': sample_annotation_tokens" in text
    assert "'instance_tokens': instance_tokens" in text
