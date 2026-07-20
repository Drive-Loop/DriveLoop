"""Offline rung-2 offset sweep on UNMEASURED windows.

One single-pass render per (window, candidate_offset) with the loop's
attempt-2 recipe preloaded via the manifest condition (size_scale 1.5,
num_inf_steps 50) plus the dims env, then v10b rescore in-run. Measures
which neighboring source frame makes the maneuver direction measurable
(>= 3 target-class detection frames in the selected view) instead of
the loop's fixed offset 1. Loop protocol (T=3) unchanged."""
import glob, json, os, subprocess, sys

WINDOWS = [
    ("candidate1313", "experiments/manifests/v10_night_truck.json"),
    ("candidate2751", "experiments/manifests/v10_rain_truck.json"),
    ("candidate41", "experiments/manifests/v10_bicycle.json"),
]
OFFSETS = [1, 2, 3, 4]


def main():
    rows = []
    for cand, manifest_path in WINDOWS:
        base = sorted(glob.glob("outputs/driveloop/%s*baseline*" % cand))
        base = [b for b in base if "official" in b] or base
        if not base:
            print("MISSING_BASELINE %s" % cand)
            continue
        baseline_dir = base[0]
        case = json.load(open(manifest_path))["cases"][0]
        for off in OFFSETS:
            out_dir = "outputs/driveloop/%s_rebind_sweep_off%d" % (cand, off)
            man = "/tmp/sweep_%s_off%d.json" % (cand, off)
            json.dump({"cases": [{
                "name": "%s_off%d" % (case["name"], off),
                "prompt": case["prompt"],
                "condition": {
                    "structural_escalation": {"level": 2, "size_scale": 1.5,
                                              "proximity_scale": 1.0,
                                              "reason": "offset_sweep"},
                    "generation_escalation": {"level": 2, "num_inf_steps": 50},
                    "source_rebinding": {"candidate_offset": off,
                                         "reason": "offset_sweep"},
                },
            }]}, open(man, "w"))
            if glob.glob(out_dir + "/*/result.json"):
                print("SKIP_DONE %s off%d" % (cand, off))
            else:
                env = dict(os.environ)
                env.update({"DRIVELOOP_EGO_INJECTION": "1",
                            "DRIVELOOP_DD2_SEED_BANK": "0",
                            "DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE": "1.5"})
                cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
                       "--source-from-baseline-dir", baseline_dir,
                       "--cases", man, "--output-dir", out_dir,
                       "--max-iterations", "1", "--target-score", "0.99",
                       "--perception-weights", "yolov8x.pt", "--use-task-utility"]
                print("RUN %s off%d" % (cand, off)); sys.stdout.flush()
                rc = subprocess.call(cmd, env=env)
                print("RC %s off%d = %d" % (cand, off, rc)); sys.stdout.flush()
            g = glob.glob(out_dir + "/*/result.json")
            rows.append((cand, off,
                         json.load(open(g[0]))["best_evaluation"]["metrics"]
                         if g else None))
    print("SWEEP_SUMMARY")
    print("%-14s %4s %7s %5s %9s %5s %6s" % (
        "window", "off", "S_perc", "dir", "delta_x", "det", "Q_cov"))
    for cand, off, m in rows:
        if m is None:
            print("%-14s %4d  (missing)" % (cand, off))
            continue
        sp = m.get("S_perc", 0.0)
        dr = m.get("maneuver_direction_consistent")
        dx = m.get("maneuver_pixel_delta_x")
        dxs = ("%.1f" % dx) if isinstance(dx, (int, float)) else "-"
        drs = "-" if dr is None else ("%.0f" % dr)
        print("%-14s %4d %7.3f %5s %9s %5s %6s" % (
            cand, off, sp, drs, dxs,
            str(m.get("perception_detection_count")), str(m.get("Q_cov"))))


if __name__ == "__main__":
    main()
