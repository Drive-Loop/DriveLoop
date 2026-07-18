#!/usr/bin/env python
"""Pre-generation window-admission probe (Step A: C1 + C2).

Offline, read-only gate. It does NOT run the DD2 backend, does NOT touch the
GPU, and does NOT write generation artifacts. For each (window, case) it answers
two questions that are decidable before generation:

  C1  binding readiness -- does the requested source window actually bind?
      Computed by build_source_sample_binding on the window's source config
      (dataset_dir + sample/scene/instance tokens). This is the exact call the
      DD2 backend makes before the GPU subprocess, so C1 here equals C1 at run
      time. C1 is a property of the window, not of the case.

  C2  v10b measurability -- will the v10b evaluator produce a scorable view?
      A case is measurable only if grounding yields a lateral maneuver
      (cut_in / lane_change) that builds an actor_motion_surface_plan with
      target cams and a lateral side. The "approaching" primitive (m4-style
      intersection-approach prompts) deliberately builds no surface plan, so
      v10b resolves no scorable view and the case is unmeasurable. C2 reuses the
      real ManeuverViewRestrictedSuperclassEvaluator._views_to_evaluate, so it
      cannot drift from the adopted protocol.

Verdict (Step A checks C1 and C2 only):

  REJECT  C1 not ready        -- the window does not bind; do not spend GPU.
  WARN    C1 ready, C2 not     -- binds but v10b cannot score it (m4 class);
                                  repair the manifest (surface plan) or replace.
  ADMIT   C1 ready, C2 ready   -- not rejected by binding or measurability.
                                  NOTE: C3 (baseline fingerprint) and C4
                                  (baseline collision) are Step B and are not
                                  evaluated here; ADMIT is not full admission.

Source config can be given explicitly or, preferably, read from an existing
no-injection baseline run directory (--source-from-baseline-dir), so the source
tokens are taken byte-exact from the archive rather than retyped.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from driveloop.actor_motion import build_actor_motion_surface_plan
from driveloop.condition_adapter import DriveDreamer2ConditionAdapter
from driveloop.grounding import RuleBasedGrounder
from driveloop.longtail import LongTailController
from driveloop.perception_v10 import ManeuverViewRestrictedSuperclassEvaluator
from driveloop.schema import DriveLoopRequest
from driveloop.source_sample_binding import build_source_sample_binding

# Allow the module to be imported and monkeypatched in tests.
__all__ = [
    "scene_spec_for",
    "surface_plan_for",
    "c2_measurability",
    "c1_binding",
    "verdict",
    "source_config_from_baseline_dir",
    "load_cases",
    "build_report",
    "main",
]

_V10B_EVALUATOR = None


def _v10b_evaluator() -> ManeuverViewRestrictedSuperclassEvaluator:
    """A detector-free v10b evaluator, built lazily and reused. detector=None is
    safe: _views_to_evaluate never calls the detector."""
    global _V10B_EVALUATOR
    if _V10B_EVALUATOR is None:
        _V10B_EVALUATOR = ManeuverViewRestrictedSuperclassEvaluator(detector=None)
    return _V10B_EVALUATOR


def scene_spec_for(prompt: str):
    """Ground a text prompt as the runner does. multimodal_preprocessor is None
    because these cases carry no auxiliary inputs; grounding of a text-only
    prompt is identical either way."""
    grounder = RuleBasedGrounder(multimodal_preprocessor=None)
    return grounder.ground(DriveLoopRequest(prompt=prompt, condition={}, metadata={}))


def surface_plan_for(prompt: str) -> Dict[str, Any]:
    """Run the same no-GPU chain the backend runs before generation:
    grounding -> long-tail -> condition adapter -> actor-motion surface plan."""
    spec = scene_spec_for(prompt)
    condition_plan = LongTailController().build(spec, requested_tags=[], history=[])
    dd2_condition = DriveDreamer2ConditionAdapter().build(spec, condition_plan)
    actor_motion_plan = dd2_condition.executable_condition.get("actor_motion_plan", {})
    return build_actor_motion_surface_plan(actor_motion_plan)


def c2_measurability(surface_plan: Dict[str, Any]) -> Dict[str, Any]:
    """C2: does v10b resolve a scorable view for this surface plan?"""
    metadata = {"dd2_override_candidate_plan": {"actor_motion_surface_plan": surface_plan}}
    allowed = list(_v10b_evaluator()._views_to_evaluate(metadata))
    available = surface_plan.get("available") is True
    return {
        "surface_plan_available": available,
        "allowed_view_count": len(allowed),
        "allowed_views": allowed,
        "measurable": bool(available and allowed),
        "target_cam_types": list(surface_plan.get("target_cam_types") or []),
        "lateral_side": surface_plan.get("lateral_side"),
    }


def c1_binding(config: Dict[str, Any]) -> Dict[str, Any]:
    """C1: does the requested source window bind? Same call as the backend."""
    binding = build_source_sample_binding(
        config["dataset_dir"],
        source_candidate_id=config.get("source_candidate_id"),
        sample_token=config.get("sample_token"),
        scene_token=config.get("scene_token"),
        instance_token=config.get("instance_token"),
        identity_summary_path=config.get("identity_summary_path"),
        frame_num=int(config.get("frame_num", 8)),
        hz_factor=int(config.get("hz_factor", 3)),
        video_split_rate=int(config.get("video_split_rate", 1)),
        multiview=bool(config.get("multiview", True)),
    )
    return {
        "ready": binding.get("ready") is True,
        "reason": binding.get("reason"),
        "matched_sample_tokens": list(binding.get("matched_sample_tokens", []) or []),
        "matched_scene_tokens": list(binding.get("matched_scene_tokens", []) or []),
        "front_record": binding.get("front_record", {}) or {},
        "dd2_batch_skip": binding.get("dd2_batch_skip"),
    }


def verdict(c1: Dict[str, Any], c2: Dict[str, Any]) -> str:
    if not c1.get("ready"):
        return "REJECT"
    if not c2.get("measurable"):
        return "WARN"
    return "ADMIT"


def _iter_json_objects(value: Any) -> Iterable[dict]:
    """Yield every dict nested anywhere in a parsed JSON value."""
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _iter_json_objects(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_json_objects(item)


def _iter_json_documents(directory: Path):
    """Yield (document, path) for every *.json (whole file) and *.jsonl
    (one document per line) under the directory. Baseline runs archive the
    binding in result.json (v10w windows) or in history.jsonl / attempts.jsonl
    (older v9 runs), so both extensions must be read."""
    for path in sorted(directory.rglob("*.json")):
        try:
            yield json.loads(path.read_text(encoding="utf-8")), path
        except (ValueError, OSError):
            continue
    for path in sorted(directory.rglob("*.jsonl")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line), path
            except ValueError:
                continue


def _binding_to_config(binding: Any, path: Path):
    """Turn a dd2_source_sample_binding object into a source config, or None."""
    if not isinstance(binding, dict):
        return None
    selector = binding.get("selector")
    selector = selector if isinstance(selector, dict) else {}
    dataset_dir = binding.get("dataset_dir") or selector.get("dataset_dir")
    if not dataset_dir:
        return None
    return {
        "dataset_dir": dataset_dir,
        "source_candidate_id": selector.get("source_candidate_id"),
        "sample_token": selector.get("sample_token"),
        "scene_token": selector.get("scene_token"),
        "instance_token": selector.get("instance_token"),
        "identity_summary_path": selector.get("identity_summary_path"),
        "_source_metadata_path": str(path),
    }


def source_config_from_baseline_dir(directory: Path) -> Dict[str, Any]:
    """Extract the window source config (dataset_dir + selector tokens) from a
    baseline run directory's archived metadata, so tokens are read byte-exact
    from the archive rather than retyped. Reads both *.json and *.jsonl, finds a
    dd2_source_sample_binding, and prefers one whose selector carries at least
    one non-null token (falling back to the first with a dataset_dir)."""
    directory = Path(directory)
    token_keys = ("source_candidate_id", "sample_token", "scene_token", "instance_token")
    fallback = None
    for document, path in _iter_json_documents(directory):
        for obj in _iter_json_objects(document):
            config = _binding_to_config(obj.get("dd2_source_sample_binding"), path)
            if config is None:
                continue
            if any(config.get(key) for key in token_keys):
                return config
            fallback = fallback or config
    if fallback is not None:
        return fallback
    raise SystemExit("no dd2_source_sample_binding with a dataset_dir found under %s" % directory)


def load_cases(manifest_path: Path) -> List[Dict[str, Any]]:
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    rows = data["cases"] if isinstance(data, dict) and "cases" in data else data
    if not isinstance(rows, list):
        raise SystemExit("cases manifest must be a list or contain a 'cases' list")
    cases = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("name") or not row.get("prompt"):
            raise SystemExit("each case needs a name and a prompt")
        cases.append({"name": str(row["name"]), "prompt": str(row["prompt"])})
    return cases


def build_report(window_label: str, source_config: Dict[str, Any], cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    c1 = c1_binding(source_config)  # window-level, case-independent
    rows = []
    for case in cases:
        surface_plan = surface_plan_for(case["prompt"])
        c2 = c2_measurability(surface_plan)
        rows.append({
            "window": window_label,
            "case": case["name"],
            "verdict": verdict(c1, c2),
            "c1_ready": c1["ready"],
            "c2_measurable": c2["measurable"],
            "c2_allowed_view_count": c2["allowed_view_count"],
            "c2_surface_plan_available": c2["surface_plan_available"],
            "c2_target_cam_types": c2["target_cam_types"],
            "c2_lateral_side": c2["lateral_side"],
        })
    return {"window": window_label, "c1": c1, "source_config": source_config, "cases": rows}


def _print_report(report: Dict[str, Any]) -> None:
    c1 = report["c1"]
    print("window=%s  C1.ready=%s  reason=%s  batch_skip=%s"
          % (report["window"], c1["ready"], c1["reason"], c1["dd2_batch_skip"]))
    print("  matched_sample_tokens=%s  matched_scene_tokens=%s"
          % (c1["matched_sample_tokens"], c1["matched_scene_tokens"]))
    print("  %-30s %-8s %-14s %-14s %s" % ("case", "verdict", "c2_measurable", "allowed_views", "target/side"))
    for r in report["cases"]:
        print("  %-30s %-8s %-14s %-14s %s/%s"
              % (r["case"], r["verdict"], r["c2_measurable"], r["c2_allowed_view_count"],
                 r["c2_target_cam_types"], r["c2_lateral_side"]))
    verdicts = [r["verdict"] for r in report["cases"]]
    print("  summary: ADMIT=%d WARN=%d REJECT=%d"
          % (verdicts.count("ADMIT"), verdicts.count("WARN"), verdicts.count("REJECT")))
    print("  NOTE: Step A checks C1+C2 only; ADMIT is not full admission "
          "(C3 fingerprint and C4 baseline-collision are Step B).")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Pre-generation window-admission probe (Step A: C1 binding + C2 v10b measurability). Read-only, no GPU."
    )
    parser.add_argument("--cases-manifest", required=True, type=Path,
                        help="JSON manifest with cases[].name and cases[].prompt")
    parser.add_argument("--source-from-baseline-dir", type=Path, default=None,
                        help="read the window source config from a baseline run dir's archived metadata")
    parser.add_argument("--dataset-dir", default=None)
    parser.add_argument("--source-candidate-id", default=None)
    parser.add_argument("--sample-token", default=None)
    parser.add_argument("--scene-token", default=None)
    parser.add_argument("--instance-token", default=None)
    parser.add_argument("--identity-summary-path", default=None)
    parser.add_argument("--window-label", default=None)
    parser.add_argument("--output-jsonl", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.source_from_baseline_dir is not None:
        source_config = source_config_from_baseline_dir(args.source_from_baseline_dir)
    elif args.dataset_dir:
        source_config = {
            "dataset_dir": args.dataset_dir,
            "source_candidate_id": args.source_candidate_id,
            "sample_token": args.sample_token,
            "scene_token": args.scene_token,
            "instance_token": args.instance_token,
            "identity_summary_path": args.identity_summary_path,
        }
    else:
        parser.error("provide --source-from-baseline-dir or --dataset-dir")

    window_label = args.window_label or source_config.get("source_candidate_id") or "window"
    cases = load_cases(args.cases_manifest)
    report = build_report(window_label, source_config, cases)
    _print_report(report)

    if args.output_jsonl is not None:
        args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.output_jsonl.open("w", encoding="utf-8") as handle:
            for row in report["cases"]:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
