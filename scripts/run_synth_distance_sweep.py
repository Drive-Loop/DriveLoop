"""Distance sweep for the synthetic-trajectory rung on floored windows.

One single-pass render per (window, longitudinal_base_m) with the
synthetic rung requested via condition and the escalation recipe fixed
(size 1.5, steps 50, lateral_base_m 3.5). Zero code change: the surface
plan already honors absolute escalation overrides. Measures whether a
closer synthetic actor becomes detectable under degraded conditions."""
import glob, json, os, subprocess, sys

WINDOWS = [
    ("candidate1313", "experiments/manifests/v10_night_truck.json"),
    ("candidate2751", "experiments/manifests/v10_rain_truck.json"),
    ("candidate41", "experiments/manifests/v10_bicycle.json"),
    ("candidate1300", "experiments/manifests/v10_night.json"),
]
DISTANCES = [9.0, 12.0, 15.0, 20.0]


def main():
    rows = []
    for cand, manifest in WINDOWS:
        base = sorted(glob.glob("outputs/driveloop/%s*baseline*" % cand))
        base = [b for b in base if "official" in b] or base
        if not base:
            print("MISSING_BASELINE", cand)
            continue
        case = json.load(open(manifest))["cases"][0]
        for dist in DISTANCES:
            tag = str(dist).replace(".0", "")
            out_dir = "outputs/driveloop/%s_synth_dist%s" % (cand, tag)
            man = "/tmp/synth_%s_d%s.json" % (cand, tag)
            json.dump({"cases": [{
                "name": "%s_d%s" % (case["name"], tag),
                "prompt": case["prompt"],
                "condition": {
                    "structural_escalation": {"level": 2, "size_scale": 1.5,
                                              "proximity_scale": 1.0,
                                              "lateral_base_m": 3.5,
                                              "longitudinal_base_m": dist,
                                              "reason": "distance_sweep"},
                    "generation_escalation": {"level": 2, "num_inf_steps": 50},
                    "synthetic_trajectory_escalation": {"level": 2,
                                                        "reason": "distance_sweep"},
                },
            }]}, open(man, "w"))
            if glob.glob(out_dir + "/*/result.json"):
                print("SKIP_DONE %s d%s" % (cand, tag))
            else:
                env = dict(os.environ)
                env.update({"DRIVELOOP_EGO_INJECTION": "1",
                            "DRIVELOOP_DD2_SEED_BANK": "0"})
                cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
                       "--source-from-baseline-dir", base[0],
                       "--cases", man, "--output-dir", out_dir,
                       "--max-iterations", "1", "--target-score", "0.99",
                       "--perception-weights", "yolov8x.pt", "--use-task-utility"]
                print("RUN %s d%s" % (cand, tag)); sys.stdout.flush()
                rc = subprocess.call(cmd, env=env)
                print("RC %s d%s = %d" % (cand, tag, rc)); sys.stdout.flush()
            g = glob.glob(out_dir + "/*/result.json")
            rows.append((cand, dist,
                         json.load(open(g[0]))["best_evaluation"]["metrics"]
                         if g else None))
    print("DIST_SWEEP_SUMMARY")
    print("%-14s %6s %7s %5s %9s %5s %6s" % (
        "window", "dist", "S_perc", "dir", "delta_x", "det", "Q_cov"))
    for cand, dist, m in rows:
        if m is None:
            print("%-14s %6.0f  (missing)" % (cand, dist))
            continue
        dr = m.get("maneuver_direction_consistent")
        dx = m.get("maneuver_pixel_delta_x")
        print("%-14s %6.0f %7.3f %5s %9s %5s %6s" % (
            cand, dist, m.get("S_perc", 0.0),
            "-" if dr is None else ("%.0f" % dr),
            ("%.1f" % dx) if isinstance(dx, (int, float)) else "-",
            str(m.get("perception_detection_count")), str(m.get("Q_cov"))))


if __name__ == "__main__":
    main()
