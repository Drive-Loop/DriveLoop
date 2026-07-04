from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    return {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value.lower()}
    if isinstance(value, dict):
        return {str(k).lower() for k, v in value.items() if v}
    if isinstance(value, (list, tuple, set)):
        return {str(item).lower() for item in value if item is not None}
    return {str(value).lower()}


@dataclass
class SourceCandidateScore:
    candidate_id: str
    score: float
    matched: dict[str, list[str]] = field(default_factory=dict)
    missing: dict[str, list[str]] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)
    candidate: dict[str, Any] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.score > 0.0 and not self.missing.get("required_objects")


def requested_objects(scene_spec: Any, condition_plan: Any) -> set[str]:
    scene = as_dict(scene_spec)
    condition = as_dict(condition_plan)

    objects: set[str] = set()

    for obj in as_list(scene.get("objects")):
        if isinstance(obj, dict):
            value = obj.get("category") or obj.get("type") or obj.get("label") or obj.get("name")
            if value:
                objects.add(str(value).lower())
        elif obj:
            objects.add(str(obj).lower())

    objects.update(as_set(scene.get("target_objects")))
    objects.update(as_set(scene.get("object_categories")))

    support = as_dict(condition.get("target_object_support"))
    objects.update(as_set(support.get("required_categories")))
    objects.update(as_set(support.get("categories")))

    return objects


def requested_tags(scene_spec: Any, condition_plan: Any) -> set[str]:
    scene = as_dict(scene_spec)
    condition = as_dict(condition_plan)

    tags = set()
    tags.update(as_set(scene.get("tags")))
    tags.update(as_set(scene.get("weather")))
    tags.update(as_set(scene.get("lighting")))
    tags.update(as_set(scene.get("environment")))
    tags.update(as_set(condition.get("tags")))
    tags.update(as_set(condition.get("long_tail_tags")))
    tags.update(as_set(condition.get("resolved_tags")))
    return tags


def requested_motion(scene_spec: Any, condition_plan: Any) -> set[str]:
    scene = as_dict(scene_spec)
    condition = as_dict(condition_plan)

    motion = set()
    motion.update(as_set(scene.get("motions")))
    motion.update(as_set(scene.get("motion_primitives")))
    motion.update(as_set(condition.get("motion_primitives")))

    maneuver = as_dict(condition.get("maneuver"))
    motion.update(as_set(maneuver.get("type")))
    motion.update(as_set(maneuver.get("required_motion")))

    return motion


def candidate_values(candidate: dict[str, Any], keys: list[str]) -> set[str]:
    values = set()
    for key in keys:
        values.update(as_set(candidate.get(key)))
    return values


def overlap_score(required: set[str], available: set[str]) -> tuple[float, list[str], list[str]]:
    if not required:
        return 1.0, [], []
    matched = sorted(required & available)
    missing = sorted(required - available)
    return len(matched) / len(required), matched, missing


def score_source_candidate(
    candidate: dict[str, Any],
    scene_spec: Any,
    condition_plan: Any,
    *,
    weights: dict[str, float] | None = None,
) -> SourceCandidateScore:
    weights = weights or {
        "object": 0.40,
        "tag": 0.25,
        "motion": 0.20,
        "map": 0.10,
        "identity": 0.05,
    }

    candidate_id = str(candidate.get("candidate_id") or candidate.get("id") or candidate.get("name") or "unknown")

    req_objects = requested_objects(scene_spec, condition_plan)
    req_tags = requested_tags(scene_spec, condition_plan)
    req_motion = requested_motion(scene_spec, condition_plan)

    cand_objects = candidate_values(candidate, ["objects", "object_categories", "labels", "target_objects"])
    cand_tags = candidate_values(candidate, ["tags", "weather", "lighting", "environment", "long_tail_tags"])
    cand_motion = candidate_values(candidate, ["motions", "motion_primitives", "maneuvers"])

    object_score, object_matched, object_missing = overlap_score(req_objects, cand_objects)
    tag_score, tag_matched, tag_missing = overlap_score(req_tags, cand_tags)
    motion_score, motion_matched, motion_missing = overlap_score(req_motion, cand_motion)

    has_map = bool(candidate.get("has_hdmap") or candidate.get("map_available") or candidate.get("lane_geometry_available"))
    needs_map = bool(req_motion or {"lane_change", "cut_in", "cut-in"} & req_tags)
    map_score = 1.0 if not needs_map or has_map else 0.0

    has_identity = bool(candidate.get("has_actor_identity") or candidate.get("actor_identity_available"))
    needs_identity = bool(req_objects or req_motion)
    identity_score = 1.0 if not needs_identity or has_identity else 0.0

    score = (
        weights["object"] * object_score
        + weights["tag"] * tag_score
        + weights["motion"] * motion_score
        + weights["map"] * map_score
        + weights["identity"] * identity_score
    )

    matched = {
        "objects": object_matched,
        "tags": tag_matched,
        "motion": motion_matched,
    }
    missing = {
        "required_objects": object_missing,
        "tags": tag_missing,
        "motion": motion_missing,
    }

    diagnostics = []
    if object_missing:
        diagnostics.append("candidate_missing_required_objects")
    if tag_missing:
        diagnostics.append("candidate_missing_requested_long_tail_tags")
    if motion_missing:
        diagnostics.append("candidate_missing_requested_motion")
    if needs_map and not has_map:
        diagnostics.append("candidate_missing_map_or_lane_geometry")
    if needs_identity and not has_identity:
        diagnostics.append("candidate_missing_actor_identity")

    return SourceCandidateScore(
        candidate_id=candidate_id,
        score=round(score, 6),
        matched=matched,
        missing=missing,
        diagnostics=diagnostics,
        candidate=dict(candidate),
    )


def rank_source_candidates(
    candidates: list[dict[str, Any]],
    scene_spec: Any,
    condition_plan: Any,
    *,
    top_k: int | None = None,
) -> dict[str, Any]:
    scored = [
        score_source_candidate(candidate, scene_spec, condition_plan)
        for candidate in candidates
    ]
    scored.sort(key=lambda item: (-item.score, item.candidate_id))

    if top_k is not None:
        scored = scored[:top_k]

    rows = [
        {
            "candidate_id": item.candidate_id,
            "score": item.score,
            "ready": item.ready,
            "matched": item.matched,
            "missing": item.missing,
            "diagnostics": item.diagnostics,
            "candidate": item.candidate,
        }
        for item in scored
    ]

    best = rows[0] if rows else None

    return {
        "schema_version": "driveloop_source_candidate_ranking.v0",
        "candidate_count": len(candidates),
        "ranked_count": len(rows),
        "best_candidate_id": best.get("candidate_id") if best else None,
        "best_score": best.get("score") if best else None,
        "ready": bool(best and best.get("ready")),
        "ranked_candidates": rows,
        "claim_boundary": {
            "source_ranking_is_not_gpu_approval": True,
            "source_ranking_is_not_video_semantic_success": True,
            "source_ranking_scores_metadata_compatibility_only": True,
        },
    }
