import sys
from pathlib import Path

import numpy as np
from PIL import Image
from torchvision import transforms


def load_transform_class():
    package_root = Path("dreamer-train/projects/DriveDreamer2").resolve()
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from drivedreamer2.drivedreamer2_transforms import DriveDreamer2_Transform

    return DriveDreamer2_Transform


def make_transform():
    transform_cls = load_transform_class()
    transform = transform_cls.__new__(transform_cls)
    transform.resolution = (8, 8)
    transform.is_train = False
    transform.box_normal = False
    transform.text_embed_dim = 4
    transform.prompt_embed_map = {"realistic autonomous driving scene.": np.ones((1, 4), dtype=np.float32)}
    transform.transform = transforms.ToTensor()
    transform.box_transform = transforms.ToTensor()
    transform.driveloop_override = None
    transform.gd_input_name = "image_hdmap"
    transform.bd_input_name = "image_box"
    transform.img_mask_num = 0
    transform.img_mask_type = None
    transform.name_map = {"vehicle.motorcycle": 0}
    transform.box_skeleton = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7],
    ]
    return transform


def test_motion_metadata_reports_identity_fields_from_data_dict():
    transform = make_transform()
    data_dict = {
        "image": Image.new("RGB", (8, 8)),
        "image_hdmap": Image.new("RGB", (8, 8)),
        "boxes3d": np.array([[0.0, 0.0, 10.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0]], dtype=np.float32),
        "corners": np.zeros((1, 8, 2), dtype=np.float32),
        "labels3d": ["vehicle.motorcycle"],
        "ori_labels3d": ["vehicle.motorcycle"],
        "velocities": np.zeros((1, 2), dtype=np.float32),
        "scene_description": "prompt",
        "frame_idx": 0,
        "cam_type": "cam_front",
        "calib": {"cam_intrinsic": np.eye(3, dtype=np.float32)},
        "video_length": 1,
        "sample_annotation_tokens": ["ann_0"],
        "instance_tokens": ["inst_0"],
    }

    output = transform(data_dict)
    metadata = output["motion_metadata"]

    assert metadata["actor_identity_available_in_batch"] is True
    assert metadata["actor_identity_fields"] == ["instance_tokens", "sample_annotation_tokens"]
    assert metadata["velocities_available_in_batch"] is True
    assert metadata["boxes3d_available_in_batch"] is True
    assert metadata["claim"] == "metadata_observed_only_not_runtime_control"
