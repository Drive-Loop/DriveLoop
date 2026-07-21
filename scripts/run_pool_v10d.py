"""Re-run the six-window pool closed-loop under the fixed protocol (v10d):
category-correct refiner additions + formal synthetic-trajectory rung-2.
Same evaluator as v10b, same windows and manifests, bank0, T=3."""
import glob, json, os, subprocess, sys

RUNS = [
    ("candidate1677", "experiments/manifests/v10_truck.json", "truck_cut_in_v10d"),
    ("candidate1313", "experiments/manifests/v10_night_truck.json", "night_truck_v10d"),
    ("candidate2751", "experiments/manifests/v10_rain_truck.json", "rain_truck_v10d"),
    ("candidate1300", "experiments/manifests/v10_night.json", "night_cut_in_v10d"),
    ("candidate28", "experiments/manifests/v10_bus.json", "bus_v10d"),
    ("candidate41", "experiments/manifests/v10_bicycle.json", "bicycle_v10d"),
]

SHORT = {"source_bound_real_track_ego": "REAL",
         "ego_frame_one_entry_per_video_frame": "SYN"}


def fk(o, k, out):
    if isinstance(o, dict):
        if k in o:
            out.append(o[k])
        for v in o.values():
            fk(v, k, out)
    elif isinstance(o, list):
        for v in o:
            fk(v, k, out)


def main():
    for cand, manifest, tag in RUNS:
        base = sorted(glob.glob("outputs/driveloop/%s*baseline*" % cand))
        base = [b for b in base if "official" in b] or base
        if not base:
            print("MISSING_BASELINE", cand)
            continue
        out_dir = "outputs/driveloop/%s_%s" % (cand, tag)
        if glob.glob(out_dir + "/*/result.json"):
            print("SKIP_DONE", out_dir)
            continue
        env = dict(os.environ)
        env.update({"DRIVELOOP_EGO_INJECTION": "1", "DRIVELOOP_DD2_SEED_BANK": "0"})
        cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
               "--source-from-baseline-dir", base[0], "--cases", manifest,
               "--output-dir", out_dir, "--max-iterations", "3",
               "--target-score", "0.99",
               "--perception-weights", "yolov8x.pt", "--use-task-utility"]
        print("RUN", out_dir)
        sys.stdout.flush()
        rc = subprocess.call(cmd, env=env)
        print("RC %s = %d" % (out_dir, rc))
        sys.stdout.flush()
    print("V10C_SUMMARY")
    print("%-32s %-10s %-5s %s" % ("run", "best", "dir", "attempts (S_perc/dir/path/cat)"))
    for cand, manifest, tag in RUNS:
        g = glob.glob("outputs/driveloop/%s_%s/*/result.json" % (cand, tag))
        if not g:
            print("%-32s (missing)" % ("%s_%s" % (cand, tag)))
            continue
        res = json.load(open(g[0]))
        best = (res.get("best_evaluation") or {}).get("metrics") or {}
        atts = []
        for i, att in enumerate(res.get("attempt_history") or []):
            m = (att.get("evaluation") or {}).get("metrics") or {}
            maps, plans = [], []
            fk(att, "actor_motion_frame_mapping", maps)
            fk(att, "actor_motion_surface_plan", plans)
            mode = SHORT.get(maps[0].get("mode"), "?") if maps else "?"
            cat = (plans[0].get("target_actor") or {}).get("category") if plans else "?"
            dr = m.get("maneuver_direction_consistent")
            atts.append("a%d:%.3f/%s/%s/%s" % (
                i, float(m.get("S_perc") or 0.0),
                "-" if dr is None else "%.0f" % dr, mode, str(cat)[:5]))
        dr = best.get("maneuver_direction_consistent")
        print("%-32s best=%.3f %-5s %s" % (
            "%s_%s" % (cand, tag), float(best.get("S_perc") or 0.0),
            "-" if dr is None else str(dr), "  ".join(atts)))


main()
