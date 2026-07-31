"""Rung-1-only loop (T=4, structural escalation kept, synthetic rung
disabled) on the seven-arm family and the six-window pool, for the
cumulative module ablation."""
import glob, json, os, subprocess, sys

from scripts.run_seven_arms_v10f import ARMS, CASES

POOL = [
    ("candidate1677", "experiments/manifests/v10_truck.json", "truck_cut_in"),
    ("candidate1313", "experiments/manifests/v10_night_truck.json", "night_truck"),
    ("candidate2751", "experiments/manifests/v10_rain_truck.json", "rain_truck"),
    ("candidate1300", "experiments/manifests/v10_night.json", "night_cut_in"),
    ("candidate28", "experiments/manifests/v10_bus.json", "bus"),
    ("candidate41", "experiments/manifests/v10_bicycle.json", "bicycle"),
]


def sp(m):
    return float((m or {}).get("S_perc") or 0.0)


def render(baseline, cases, out_dir, arm_env):
    env = dict(os.environ)
    env.update({"DRIVELOOP_EGO_INJECTION": "1",
                "DRIVELOOP_DD2_SEED_BANK": "0",
                "DRIVELOOP_DISABLE_SYNTHETIC_RUNG": "1"})
    env.update(arm_env)
    cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
           "--source-from-baseline-dir", baseline, "--cases", cases,
           "--output-dir", out_dir, "--max-iterations", "4",
           "--target-score", "0.99",
           "--perception-weights", "yolov8x.pt", "--use-task-utility"]
    print("RUN", out_dir)
    sys.stdout.flush()
    rc = subprocess.call(cmd, env=env)
    print("RC %s = %d" % (out_dir, rc))
    sys.stdout.flush()


def main():
    for tag, baseline, arm_env in ARMS:
        short = tag.replace("cl_v10f_", "")
        out = "outputs/driveloop/cl_r1_%s" % short
        if glob.glob(out + "/*/result.json"):
            print("SKIP_DONE", out)
        else:
            render(baseline, CASES, out, arm_env)
    for cand, manifest, tag in POOL:
        base = sorted(glob.glob("outputs/driveloop/%s_baseline_official" % cand))
        out = "outputs/driveloop/%s_%s_r1" % (cand, tag)
        if glob.glob(out + "/*/result.json"):
            print("SKIP_DONE", out)
        elif base:
            render(base[0], manifest, out, {})
    print("RUNG1_ABLATION_SUMMARY")
    tot, n = 0.0, 0
    for tag, baseline, arm_env in ARMS:
        short = tag.replace("cl_v10f_", "")
        vals = []
        for rj in sorted(glob.glob("outputs/driveloop/cl_r1_%s/*/result.json" % short)):
            vals.append(sp(((json.load(open(rj)).get("best_evaluation")
                            or {}).get("metrics")) or {}))
        m = sum(vals) / max(len(vals), 1)
        tot += m
        n += 1
        print("  %-24s %.3f" % (short, m))
    print("FAMILY_R1_GRAND %.3f" % (tot / max(n, 1)))
    vals = []
    for cand, manifest, tag in POOL:
        g = glob.glob("outputs/driveloop/%s_%s_r1/*/result.json" % (cand, tag))
        v = sp(((json.load(open(g[0])).get("best_evaluation")
                 or {}).get("metrics")) if g else {})
        vals.append(v)
        print("  %-24s %.3f" % (cand, v))
    print("POOL_R1_MEAN %.3f" % (sum(vals) / max(len(vals), 1)))


if __name__ == "__main__":
    main()
