"""Seed distribution of the escalated recipe (rung-1/2 settings).

One single-pass render per (window, seed bank) with the escalated recipe
preloaded via the manifest condition (size_scale 1.5, num_inf_steps 50).
No source_rebinding (proven no-op), no dims env. Together with the loop's
attempt 1/2 (seeds 1 and 2 at bank 0) this yields 5 escalated seeds per
window, quantifying reseed-under-escalation honestly."""
import glob, json, os, subprocess, sys

WINDOWS = [
    ("candidate1677", "experiments/manifests/v10_truck.json"),
    ("candidate1313", "experiments/manifests/v10_night_truck.json"),
    ("candidate2751", "experiments/manifests/v10_rain_truck.json"),
    ("candidate41", "experiments/manifests/v10_bicycle.json"),
]
BANKS = [3, 4, 5]


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
        for bank in BANKS:
            out_dir = "outputs/driveloop/%s_rung2_seed_bank%d" % (cand, bank)
            man = "/tmp/rung2_%s_bank%d.json" % (cand, bank)
            json.dump({"cases": [{
                "name": "%s_bank%d" % (case["name"], bank),
                "prompt": case["prompt"],
                "condition": {
                    "structural_escalation": {"level": 2, "size_scale": 1.5,
                                              "proximity_scale": 1.0,
                                              "reason": "seed_distribution"},
                    "generation_escalation": {"level": 2, "num_inf_steps": 50},
                },
            }]}, open(man, "w"))
            if glob.glob(out_dir + "/*/result.json"):
                print("SKIP_DONE %s bank%d" % (cand, bank))
            else:
                env = dict(os.environ)
                env.update({"DRIVELOOP_EGO_INJECTION": "1",
                            "DRIVELOOP_DD2_SEED_BANK": str(bank)})
                cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
                       "--source-from-baseline-dir", baseline_dir,
                       "--cases", man, "--output-dir", out_dir,
                       "--max-iterations", "1", "--target-score", "0.99",
                       "--perception-weights", "yolov8x.pt", "--use-task-utility"]
                print("RUN %s bank%d" % (cand, bank)); sys.stdout.flush()
                rc = subprocess.call(cmd, env=env)
                print("RC %s bank%d = %d" % (cand, bank, rc)); sys.stdout.flush()
            g = glob.glob(out_dir + "/*/result.json")
            rows.append((cand, bank,
                         json.load(open(g[0]))["best_evaluation"]["metrics"]
                         if g else None))
    print("SEED_DIST_SUMMARY")
    print("%-14s %5s %7s %5s %9s %5s" % (
        "window", "bank", "S_perc", "dir", "delta_x", "det"))
    for cand, bank, m in rows:
        if m is None:
            print("%-14s %5d  (missing)" % (cand, bank))
            continue
        dr = m.get("maneuver_direction_consistent")
        dx = m.get("maneuver_pixel_delta_x")
        print("%-14s %5d %7.3f %5s %9s %5s" % (
            cand, bank, m.get("S_perc", 0.0),
            "-" if dr is None else ("%.0f" % dr),
            ("%.1f" % dx) if isinstance(dx, (int, float)) else "-",
            str(m.get("perception_detection_count"))))


if __name__ == "__main__":
    main()
