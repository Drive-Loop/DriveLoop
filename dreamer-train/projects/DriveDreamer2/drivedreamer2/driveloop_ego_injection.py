"""Compatibility shim: the ego-frame injection math moved to
driveloop.ego_injection so that both the DriveLoop backend (emission)
and the DD2 runtime override path (consumption in
driveloop.dd2_override) import one implementation. The DD2 runtime
already imports the driveloop package (see drivedreamer2_transforms),
so this indirection adds no new dependency."""
from driveloop.ego_injection import (  # noqa: F401
    cam_box9_to_ego_entry,
    cam_to_global_matrix,
    ego_entry_to_cam_box9,
)

__all__ = [
    "cam_box9_to_ego_entry",
    "cam_to_global_matrix",
    "ego_entry_to_cam_box9",
]
