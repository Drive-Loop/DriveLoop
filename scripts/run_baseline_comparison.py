"""Measured four-algorithm comparison on the six-window pool.

1) open-loop = attempt 0 of the v10f runs; 2) best-of-4 = plain
single-pass reseeds at banks 6/7/8 plus attempt 0, keep max (equal
render budget, no feedback); 3) text-only loop = T=4 with
DRIVELOOP_TEXT_ONLY_REFINER=1 (prompt feedback only); 4) DriveLoop =
v10f best. Same windows, evaluator, device."""
import glob, json, os, subprocess, sys

POOL = [
    ("candidate1677", "experiments/manifests/v10_truck.json", "truck_cut_in"),
    ("candidate1313", "experiments/manifests/v10_night_truck.json", "night_truck"),
    ("candidate2751", "experiments/manifests/v10_rain_truck.json", "rain_truck"),
    ("candidate1300", "experiments/manifests/v10_night.json", "night_cut_in"),
    ("candidate28", "experiments/manifests/v10_bus.json", "bus"),
    ("candidate41", "experiments/manifests/v10_bicycle.json", "bicycle"),
]
BANKS = [6, 7, 8]


def sperc(metrics):
    return float((metrics or {}).get("S_perc") or 0.0)


def best_metrics(res):
    return ((res.get("best_evaluation") or {}).get("metrics")) or {}


def attempt0_metrics(res):
    ah = res.get("attempt_history") or []
    if not ah:
        return {}
    return ((ah[0].get("evaluation") or {}).get("metrics")) or {}


def run(cmd, env):
    print("RUN", cmd[-1] if cmd else "?")
    sys.stdout.flush()
    rc = subprocess.call(cmd, env=env)
    print("RC =", rc)
    sys.stdout.flush()


def main():
    for cand, manifest, tag in POOL:
        base = sorted(glob.glob("outputs/driveloop/%s_baseline_official" % cand))
        if not base:
            print("MISSING_BASELINE", cand)
            continue
        for bank in BANKS:
            out = "outputs/driveloop/%s_%s_bo4_bank%d" % (cand, tag, bank)
            if glob.glob(out + "/*/result.json"):
                print("SKIP_DONE", out)
                continue
            env = dict(os.environ)
            env.update({"DRIVELOOP_EGO_INJECTION": "1",
                        "DRIVELOOP_DD2_SEED_BANK": str(bank)})
            run([sys.executable, "-u", "-m", "scripts.render_window_case",
                 "--source-from-baseline-dir", base[0], "--cases", manifest,
                 "--output-dir", out, "--max-iterations", "1",
                 "--target-score", "0.99",
                 "--perception-weights", "yolov8x.pt", "--use-task-utility"],
                env)
        out = "outputs/driveloop/%s_%s_textonly" % (cand, tag)
        if glob.glob(out + "/*/result.json"):
            print("SKIP_DONE", out)
        else:
            env = dict(os.environ)
            env.update({"DRIVELOOP_EGO_INJECTION": "1",
                        "DRIVELOOP_DD2_SEED_BANK": "0",
                        "DRIVELOOP_TEXT_ONLY_REFINER": "1"})
            run([sys.executable, "-u", "-m", "scripts.render_window_case",
                 "--source-from-baseline-dir", base[0], "--cases", manifest,
                 "--output-dir", out, "--max-iterations", "4",
                 "--target-score", "0.99",
                 "--perception-weights", "yolov8x.pt", "--use-task-utility"],
                env)
    print("COMPARISON_SUMMARY")
    print("%-14s %8s %8s %8s %8s" % ("window", "open", "bo4", "text", "ours"))
    sums = [0.0, 0.0, 0.0, 0.0]
    for cand, manifest, tag in POOL:
        v10f = glob.glob("outputs/driveloop/%s_*_v10f/*/result.json" % cand)
        res = json.load(open(v10f[0]))
        a0 = sperc(attempt0_metrics(res))
        ours = sperc(best_metrics(res))
        bo4 = a0
        for bank in BANKS:
            g = glob.glob("outputs/driveloop/%s_%s_bo4_bank%d/*/result.json"
                          % (cand, tag, bank))
            if g:
                bo4 = max(bo4, sperc(best_metrics(json.load(open(g[0])))))
        text = 0.0
        g = glob.glob("outputs/driveloop/%s_%s_textonly/*/result.json" % (cand, tag))
        if g:
            text = sperc(best_metrics(json.load(open(g[0]))))
        for i, v in enumerate((a0, bo4, text, ours)):
            sums[i] += v
        print("%-14s %8.3f %8.3f %8.3f %8.3f" % (cand, a0, bo4, text, ours))
    n = len(POOL)
    print("%-14s %8.3f %8.3f %8.3f %8.3f  (mean)" % (
        "MEAN", sums[0] / n, sums[1] / n, sums[2] / n, sums[3] / n))


if __name__ == "__main__":
    main()
