# Root cause: motorcycle-template leak drove the attempt-2 recoveries (2026-07-21)

## Causal chain (evidence: runtime-input diffs + mapping audits, blocks 317-329)
1. At the second refinement the refiner exhausts its generic additions and
   falls back to PERCEPTION_ESCALATION, whose strings hardcode "motorcycle"
   (a leftover of the motorcycle-only era).
2. In non-motorcycle windows the grounder parses the leaked phrase as a NEW
   target actor: the surface plan flips to category=motorcycle (verified:
   c1677 attempt 2 target_actor motorcycle, synthetic dims 1.2/2.1/3.3).
3. Real-track ego injection then finds no motorcycle in the truck/bicycle
   window (real_track_fallback_reason=no_real_track_boxes_for_category) and
   silently falls back to SYNTHETIC close-range trajectory injection
   (mode ego_frame_one_entry_per_video_frame).
4. The synthetic close-range cut-in box is what recovers detectability.
   candidate_offset remains a modulo no-op throughout (correction record 1).

## Scope
- CLEAN (verified REAL/motorcycle on all 35 x 3 attempts): the seven-arm
  motorcycle family (+0.098), Table 4 seed-only control, bank1 replication,
  determinism, and the night-motorcycle floor.
- CONFOUNDED: every attempt-2 recovery in Table 3 and Table 5
  (truck day/night/rain, bicycle): mechanism is template leak -> category
  hijack -> synthetic injection, not source rebinding.
- Seed-distribution runs (banks 3-5, all low/zero) rendered the escalated
  recipe WITHOUT the leak, confirming the recovery requires the synthetic
  injection, not the seed.

## Decision (user-approved)
Fix the leak and make the accidental mechanism deliberate and honest:
1. PERCEPTION_ESCALATION and alignment additions parameterized by the
   requested category (never change the object class).
2. Replace the no-op source_rebinding emission with an explicit
   condition["synthetic_trajectory_escalation"] rung; the backend skips
   real-track mapping only when this rung is requested and records
   real_track_fallback_reason=synthetic_trajectory_escalation_requested.
3. Re-run the six-window pool closed-loop under the fixed protocol (v10c
   run tag; evaluator unchanged) and re-measure Tables 3/5 honestly.
Paper Sec. 4.3/4.5 rebinding narrative will be rewritten after the v10c
numbers land. Prompt strings change under the fix, so v10c is a new
protocol tag; v10b artifacts remain on disk for provenance.
