from pathlib import Path

from scripts.run_runtime_surface_code_audit import build_runtime_surface_code_audit


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_runtime_surface_code_audit_records_negative_motion_surface(tmp_path):
    write(
        tmp_path / "dreamer-datasets/dd_scripts/converters/nuscenes_converter.py",
        "box_velocity\n'velocities': velocities\n'lane'\nimage_hdmap\nget_map_geom\n",
    )
    write(
        tmp_path / "dreamer-train/projects/DriveDreamer2/configs/drivedreamer2_img_cond_mini_local.py",
        "gd_input_name='image_hdmap'\nbd_input_name='image_box'\n",
    )
    write(
        tmp_path / "dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_transforms.py",
        "data_dict['boxes3d']\ngenerate_canvas_box\nnew_data_dict['box_downsampler_input']\n",
    )
    write(
        tmp_path / "dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_tester.py",
        "'grounding_downsampler_input': grounding_downsampler_input\n"
        "'box_downsampler_input': box_downsampler_input\n"
        '"grounding_downsampler_input": tensor_summary\n'
        '"box_downsampler_input": tensor_summary\n',
    )
    write(
        tmp_path / "dreamer-models/dreamer_models/pipelines/drivedreamer2/pipeline_drivedreamer2.py",
        "input_dict.get('grounding_downsampler_input'\n"
        "input_dict.get('box_downsampler_input'\n"
        "self.grounding_downsampler(grounding_downsampler_input)\n"
        "self.box_downsampler(box_downsampler_input)\n",
    )
    write(
        tmp_path / "dreamer-models/dreamer_models/models/drivedreamer2/unet_spatio_temporal_condition.py",
        'input_dict["grounding_downsampler_latents"]\n'
        'input_dict["box_downsampler_latents"]\n'
        "torch.cat([sample, grounding_downsampler_latents,box_downsampler_latents]\n",
    )

    audit = build_runtime_surface_code_audit(tmp_path)

    assert audit["status"] == "not_runtime_connected"
    assert audit["does_not_run_gpu"] is True
    assert audit["semantic_success_claim_allowed"] is False
    assert audit["surfaces"]["dataset_velocity"]["status"] == "available_in_converter"
    assert audit["surfaces"]["dataset_lane_hdmap"]["status"] == "rasterized_image_hdmap_from_lane_geometry"
    assert audit["surfaces"]["runtime_condition_inputs"]["status"] == "image_hdmap_and_image_box_downsamplers"
    assert audit["surfaces"]["static_box_canvas"]["status"] == "observed"
    assert audit["surfaces"]["dd2_runtime_input_dict"]["status"] == "downsamplers_only"
    assert audit["surfaces"]["direct_motion_runtime_surface"]["status"] == "not_observed"
    assert audit["claim_boundary"]["dataset_velocity_is_not_runtime_motion_control"] is True
