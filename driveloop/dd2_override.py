from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


_CATEGORY_TO_ORI_LABEL = {
    "animal": "animal",
    "pedestrian": "human.pedestrian.adult",
    "bicycle": "vehicle.bicycle",
    "motorcycle": "vehicle.motorcycle",
    "car": "vehicle.car",
    "truck": "vehicle.truck",
    "bus": "vehicle.bus.rigid",
    "barrier": "movable_object.barrier",
}

_CATEGORY_TO_LABEL3D = {
    "pedestrian": ["human", "pedestrian", "adult"],
    "bicycle": ["vehicle", "bicycle"],
    "motorcycle": ["vehicle", "motorcycle"],
    "car": ["vehicle", "car"],
    "truck": ["vehicle", "truck"],
    "bus": ["vehicle", "bus", "rigid"],
    "barrier": ["movable_object", "barrier"],
    "animal": ["animal"],
}


def apply_dd2_override_to_sample(
    data_dict: dict[str, Any],
    override_spec: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(override_spec, dict) or not override_spec:
        return data_dict, {"available": False, "reason": "missing_override_spec"}

    updated = dict(data_dict)
    audit: dict[str, Any] = {
        "available": True,
        "schema_version": override_spec.get("schema_version"),
        "applied": [],
        "skipped": [],
        "signatures_before": {
            "boxes3d": tensor_signature(data_dict.get("boxes3d")),
            "image_hdmap": tensor_signature(data_dict.get("image_hdmap")),
            "scene_description": data_dict.get("scene_description"),
        },
        "signatures_after": {},
    }

    scene_description = override_spec.get("scene_description", {})
    if isinstance(scene_description, dict) and scene_description.get("value"):
        updated["scene_description"] = str(scene_description["value"])
        audit["applied"].append({
            "target": "scene_description",
            "mode": "replace",
            "source": scene_description.get("source", "unknown"),
        })

    boxes3d = override_spec.get("boxes3d", {})
    append_entries = boxes3d.get("append") if isinstance(boxes3d, dict) else None
    if append_entries:
        updated, boxes_audit = _append_boxes3d(updated, append_entries)
        audit["applied"].append(boxes_audit)
    else:
        audit["skipped"].append({"target": "boxes3d", "reason": "no_append_entries"})

    image_hdmap = override_spec.get("image_hdmap", {})
    if isinstance(image_hdmap, dict) and image_hdmap.get("mode") == "zero":
        updated, hdmap_audit = _zero_image_hdmap(updated, image_hdmap)
        audit["applied"].append(hdmap_audit)
    elif isinstance(image_hdmap, dict) and image_hdmap.get("mode") == "replace_from_path":
        updated, hdmap_audit = _replace_image_hdmap_from_path(updated, image_hdmap)
        if hdmap_audit.get("applied") is True:
            audit["applied"].append(hdmap_audit)
        else:
            audit["skipped"].append(hdmap_audit)
    else:
        reason = image_hdmap.get("reason", "no_verified_hdmap_override") if isinstance(image_hdmap, dict) else "missing_hdmap_override"
        audit["skipped"].append({"target": "image_hdmap", "reason": reason})

    audit["signatures_after"].update({
        "boxes3d": tensor_signature(updated.get("boxes3d")),
        "image_hdmap": tensor_signature(updated.get("image_hdmap")),
        "scene_description": updated.get("scene_description"),
    })
    audit["changed"] = {
        key: audit["signatures_before"].get(key) != audit["signatures_after"].get(key)
        for key in ("boxes3d", "image_hdmap", "scene_description")
    }
    audit["image_box_expected_changed"] = bool(audit["changed"].get("boxes3d"))
    return updated, audit


def tensor_signature(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        array = np.asarray(value)
    except Exception:
        return {"type": type(value).__name__, "repr": repr(value)[:120]}
    contiguous = np.ascontiguousarray(array)
    return {
        "type": type(value).__name__,
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "sum": float(np.asarray(array, dtype=np.float64).sum()) if array.size else 0.0,
        "nonzero": int(np.count_nonzero(array)) if array.size else 0,
        "sha256": hashlib.sha256(contiguous.tobytes()).hexdigest(),
    }


def write_override_audit(path: str | Path | None, audit: dict[str, Any]) -> None:
    if not path:
        return
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(audit, sort_keys=True) + "\n")


def read_override_audit(path: str | Path) -> dict[str, Any]:
    audit_path = Path(path)
    if not audit_path.exists():
        return {"available": False, "path": str(audit_path), "reason": "audit_file_not_written"}

    entries = []
    with audit_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    changed_counts: dict[str, int] = {}
    for entry in entries:
        changed_map = entry.get("changed", {})
        for target, changed in changed_map.items():
            if changed:
                changed_counts[target] = changed_counts.get(target, 0) + 1
        if "image_box" not in changed_map and entry.get("image_box_expected_changed"):
            changed_counts["image_box"] = changed_counts.get("image_box", 0) + 1

    return {
        "available": True,
        "path": str(audit_path),
        "entry_count": len(entries),
        "changed_counts": changed_counts,
        "entries_preview": entries[:3],
    }


def _append_boxes3d(data_dict: dict[str, Any], append_entries: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = dict(data_dict)
    base_boxes = np.asarray(updated.get("boxes3d", np.zeros((0, 9))), dtype=np.float32)
    if base_boxes.ndim == 1:
        base_boxes = base_boxes.reshape(1, -1)

    additions = []
    labels = list(updated.get("ori_labels3d", []))
    labels3d = list(updated.get("labels3d", []))
    accepted_entries = []
    skipped_entries = []

    for entry in append_entries:
        box = entry.get("box3d") if isinstance(entry, dict) else None
        category = entry.get("category") if isinstance(entry, dict) else None
        if not isinstance(box, list) or len(box) != 9:
            skipped_entries.append({"category": category, "reason": "box3d_must_have_9_values"})
            continue
        try:
            additions.append([float(value) for value in box])
        except (TypeError, ValueError):
            skipped_entries.append({"category": category, "reason": "box3d_values_must_be_numeric"})
            continue

        labels.append(entry.get("ori_label") or _CATEGORY_TO_ORI_LABEL.get(category, str(category)))
        labels3d.append(entry.get("label3d") or _CATEGORY_TO_LABEL3D.get(category, [str(category)]))
        accepted_entries.append({
            "category": category,
            "source": entry.get("source", "unknown"),
            "provenance": entry.get("provenance", "unknown"),
        })

    if additions:
        additions_array = np.asarray(additions, dtype=np.float32)
        updated["boxes3d"] = additions_array if base_boxes.size == 0 else np.concatenate([base_boxes, additions_array], axis=0)
        updated["ori_labels3d"] = labels
        updated["labels3d"] = labels3d

    return updated, {
        "target": "boxes3d",
        "mode": "append",
        "accepted_count": len(accepted_entries),
        "skipped_count": len(skipped_entries),
        "accepted_entries": accepted_entries,
        "skipped_entries": skipped_entries,
    }


def _zero_image_hdmap(data_dict: dict[str, Any], image_hdmap_spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = dict(data_dict)
    image_hdmap = updated.get("image_hdmap")
    if image_hdmap is None:
        return updated, {"target": "image_hdmap", "mode": "zero", "applied": False, "reason": "missing_image_hdmap"}

    if hasattr(image_hdmap, "copy") and hasattr(image_hdmap, "size") and hasattr(image_hdmap, "mode"):
        try:
            from PIL import Image
            updated["image_hdmap"] = Image.new(image_hdmap.mode, image_hdmap.size)
        except Exception:
            updated["image_hdmap"] = np.zeros_like(np.asarray(image_hdmap))
    else:
        updated["image_hdmap"] = np.zeros_like(np.asarray(image_hdmap))

    return updated, {
        "target": "image_hdmap",
        "mode": "zero",
        "applied": True,
        "source": image_hdmap_spec.get("source", "explicit_override"),
    }


def _replace_image_hdmap_from_path(
    data_dict: dict[str, Any],
    image_hdmap_spec: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = dict(data_dict)
    raster_path_value = image_hdmap_spec.get("path")
    expected_sha256 = image_hdmap_spec.get("expected_sha256")

    audit = {
        "target": "image_hdmap",
        "mode": "replace_from_path",
        "applied": False,
        "path": str(raster_path_value) if raster_path_value else None,
        "source": image_hdmap_spec.get("source", "unknown"),
        "provenance": image_hdmap_spec.get("provenance", "unknown"),
        "expected_sha256": expected_sha256,
        "claim_boundary": {
            "replacement_raster_reaches_grounding_surface_only": True,
            "hdmap_lane_geometry_override_verified": False,
            "lane_change_control_verified": False,
            "runtime_motion_control_connected": False,
            "semantic_success_claim_allowed": False,
        },
    }

    if not raster_path_value:
        audit["reason"] = "missing_path"
        return updated, audit
    if not expected_sha256:
        audit["reason"] = "missing_expected_sha256"
        return updated, audit

    raster_path = Path(str(raster_path_value))
    if not raster_path.exists():
        audit["reason"] = "missing_path"
        return updated, audit

    try:
        from PIL import Image

        replacement = Image.open(raster_path).convert(image_hdmap_spec.get("pil_mode", "RGB"))
        replacement.load()
    except Exception as exc:
        audit["reason"] = "failed_to_load_image"
        audit["error"] = str(exc)
        return updated, audit

    replacement_signature = tensor_signature(replacement)
    actual_sha256 = replacement_signature.get("sha256") if replacement_signature else None
    audit["actual_sha256"] = actual_sha256
    audit["replacement_signature"] = replacement_signature

    if actual_sha256 != expected_sha256:
        audit["reason"] = "sha256_mismatch"
        return updated, audit

    updated["image_hdmap"] = replacement
    audit["applied"] = True
    return updated, audit
