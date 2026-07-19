#!/usr/bin/env python
"""Select a source window for a user prompt (the prompt -> which source scene step).

Grounds the prompt, then ranks a candidate window pool by metadata compatibility
(driveloop.source_ranking): the objects, long-tail tags, and motion the prompt
asks for versus what each candidate window offers. This replaces manual window
binding with a prompt-driven choice.

A pool entry may carry "source_from_baseline_dir"; with --resolve-binding the
selected window's binding (dataset_dir + tokens) is read byte-exact from that
baseline directory (never retyped) so it can feed generation directly.

Ranking is metadata-only: it is not GPU approval and not a semantic-success claim.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from driveloop.grounding import RuleBasedGrounder
from driveloop.longtail import LongTailController
from driveloop.schema import DriveLoopRequest
from driveloop.source_ranking import rank_source_candidates


def ground_prompt(prompt: str):
    grounder = RuleBasedGrounder(multimodal_preprocessor=None)
    spec = grounder.ground(DriveLoopRequest(prompt=prompt, condition={}, metadata={}))
    condition_plan = LongTailController().build(spec, requested_tags=[], history=[])
    return spec, condition_plan


def _rankable_scene(spec) -> Dict[str, Any]:
    """Flatten the grounded spec into the shape source_ranking reads: the
    environment's weather/lighting values are exposed as top-level tags so a
    rainy/foggy/night prompt can prefer a window tagged for it."""
    scene = asdict(spec)
    environment = scene.get("environment", {}) or {}
    scene["weather"] = environment.get("weather")
    scene["lighting"] = environment.get("lighting")
    scene["tags"] = [
        value
        for value in (environment.get("weather"), environment.get("lighting"), environment.get("visibility"))
        if value and value not in ("unspecified", "normal")
    ]
    return scene


def select_source(prompt: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    spec, condition_plan = ground_prompt(prompt)
    return rank_source_candidates(candidates, _rankable_scene(spec), asdict(condition_plan))


def resolve_selected_binding(ranking: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Read the selected window's binding config from its baseline dir, when the
    candidate carries source_from_baseline_dir."""
    best_id = ranking.get("best_candidate_id")
    for row in ranking.get("ranked_candidates", []):
        if row.get("candidate_id") != best_id:
            continue
        baseline_dir = row.get("candidate", {}).get("source_from_baseline_dir")
        if not baseline_dir:
            return None
        from scripts.run_window_admission_probe import source_config_from_baseline_dir
        return source_config_from_baseline_dir(Path(baseline_dir))
    return None


def load_pool(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    pool = data["candidates"] if isinstance(data, dict) and "candidates" in data else data
    if not isinstance(pool, list):
        raise SystemExit("pool must be a list or contain a 'candidates' list")
    return pool


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Select a source window for a prompt by metadata ranking.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--pool", required=True, type=Path)
    parser.add_argument("--resolve-binding", action="store_true",
                        help="read the selected window's binding config from its baseline dir")
    args = parser.parse_args(argv)

    pool = load_pool(args.pool)
    ranking = select_source(args.prompt, pool)
    print("prompt: %s" % args.prompt)
    print("selected: %s (score %.4f)" % (ranking["best_candidate_id"], ranking["best_score"] or 0.0))
    for row in ranking["ranked_candidates"]:
        print("  %-18s %.4f  obj=%s tag=%s motion=%s  missing_obj=%s"
              % (row["candidate_id"], row["score"],
                 row["matched"].get("objects"), row["matched"].get("tags"),
                 row["matched"].get("motion"), row["missing"].get("required_objects")))
    if args.resolve_binding:
        binding = resolve_selected_binding(ranking)
        printable = {k: v for k, v in (binding or {}).items() if k != "_source_metadata_path"} if binding else None
        print("binding: %s" % printable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
