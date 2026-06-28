from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TENSOR_NAMES = [
    "prompt_embed",
    "box_downsampler_input",
    "grounding_downsampler_input",
    "img_cond",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def first_dict(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def nested(data: dict[str, Any], *keys: str) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def runtime_block(data: dict[str, Any]) -> dict[str, Any]:
    return first_dict(
        data.get("runtime_input_audit"),
        nested(data, "metadata", "dd2_runtime_input_audit"),
        data,
    )


def changed_counts(data: dict[str, Any]) -> dict[str, Any]:
    return first_dict(
        nested(data, "override_audit", "changed_counts"),
        nested(data, "metadata", "dd2_override_audit", "changed_counts"),
    )


def tensor_signature(runtime: dict[str, Any], name: str) -> dict[str, Any]:
    block = first_dict(runtime.get(name))
    return {
        "available": block.get("available"),
        "shape": block.get("shape"),
        "dtype": block.get("dtype"),
        "sum": block.get("sum"),
        "mean": block.get("mean"),
        "std": block.get("std"),
        "nonzero": block.get("nonzero"),
        "sha256": block.get("sha256"),
    }


def build_compare(path_a: Path, path_b: Path, label_a: str, label_b: str) -> dict[str, Any]:
    data_a = load_json(path_a)
    data_b = load_json(path_b)
    runtime_a = runtime_block(data_a)
    runtime_b = runtime_block(data_b)

    tensors = {}
    changed = {}
    for name in TENSOR_NAMES:
        sig_a = tensor_signature(runtime_a, name)
        sig_b = tensor_signature(runtime_b, name)
        is_changed = sig_a.get("sha256") != sig_b.get("sha256")
        changed[name] = is_changed
        tensors[name] = {
            label_a: sig_a,
            label_b: sig_b,
            "sha256_changed": is_changed,
        }

    return {
        "schema_version": "driveloop_dd2_runtime_hash_compare.v0",
        "inputs": {
            label_a: str(path_a),
            label_b: str(path_b),
        },
        "prompts": {
            label_a: data_a.get("prompt") or runtime_a.get("prompt_override"),
            label_b: data_b.get("prompt") or runtime_b.get("prompt_override"),
        },
        "prompt_overrides": {
            label_a: runtime_a.get("prompt_override"),
            label_b: runtime_b.get("prompt_override"),
        },
        "runtime_tensor_hash_changed": changed,
        "runtime_tensor_signatures": tensors,
        "override_changed_counts": {
            label_a: changed_counts(data_a),
            label_b: changed_counts(data_b),
        },
        "interpretation": {
            "text_condition_changed": changed.get("prompt_embed") is True,
            "box_structural_condition_changed": changed.get("box_downsampler_input") is True,
            "grounding_condition_changed": changed.get("grounding_downsampler_input") is True,
            "image_condition_changed": changed.get("img_cond") is True,
            "claim_boundary": (
                "Runtime hash comparison proves which DD2 runtime inputs changed; "
                "it does not prove generated video semantics."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", required=True, type=Path)
    parser.add_argument("--b", required=True, type=Path)
    parser.add_argument("--label-a", default="a")
    parser.add_argument("--label-b", default="b")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    report = build_compare(args.a, args.b, args.label_a, args.label_b)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
