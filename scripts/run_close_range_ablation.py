"""Why does 9 m recover at sweep seed 0 but not at loop attempt 2?

Ablates the two differences on the night-motorcycle window at a fixed
9 m synthetic rung: (a) seed bank 1/2/3 with the bare prompt, and
(b) the loop's exact refined attempt-2 prompt at bank 0."""
import glob, json, os, subprocess, sys

COND = {
    "structural_escalation": {"level": 2, "size_scale": 1.5,
                              "proximity_scale": 1.0, "lateral_base_m": 3.5,
                              "longitudinal_base_m": 9.0,
                              "reason": "close_range_ablation"},
    "generation_escalation": {"level": 2, "num_inf_steps": 50},
    "synthetic_trajectory_escalation": {"level": 2,
                                        "reason": "close_range_ablation"},
}


def main():
    base = sorted(glob.glob("outputs/driveloop/candidate1300*baseline*"))
    base = [b for b in base if "official" in b] or base
    if not base:
        print("MISSING_BASELINE")
        return
    bare = json.load(open("experiments/manifests/v10_night.json"))["cases"][0]["prompt"]
    rj = glob.glob("outputs/driveloop/candidate1300_night_cut_in_v10d/*/result.json")[0]
    res = json.load(open(rj))
    loop_prompt = (res["attempt_history"][2].get("request") or {}).get("prompt")
    print("LOOP_PROMPT: %r" % loop_prompt)
    jobs = [("bank1_bare", 1, bare), ("bank2_bare", 2, bare),
            ("bank3_bare", 3, bare), ("bank0_loopprompt", 0, loop_prompt)]
    rows = []
    for tag, bank, prompt in jobs:
        out_dir = "outputs/driveloop/candidate1300_cr9_%s" % tag
        man = "/tmp/cr9_%s.json" % tag
        json.dump({"cases": [{"name": "cr9_%s" % tag, "prompt": prompt,
                              "condition": COND}]}, open(man, "w"))
        if glob.glob(out_dir + "/*/result.json"):
            print("SKIP_DONE", tag)
        else:
            env = dict(os.environ)
            env.update({"DRIVELOOP_EGO_INJECTION": "1",
                        "DRIVELOOP_DD2_SEED_BANK": str(bank)})
            cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
                   "--source-from-baseline-dir", base[0],
                   "--cases", man, "--output-dir", out_dir,
                   "--max-iterations", "1", "--target-score", "0.99",
                   "--perception-weights", "yolov8x.pt", "--use-task-utility"]
            print("RUN", tag); sys.stdout.flush()
            rc = subprocess.call(cmd, env=env)
            print("RC %s = %d" % (tag, rc)); sys.stdout.flush()
        g = glob.glob(out_dir + "/*/result.json")
        rows.append((tag, json.load(open(g[0]))["best_evaluation"]["metrics"]
                     if g else None))
    print("CR9_ABLATION_SUMMARY")
    print("%-18s %7s %5s %5s %6s" % ("job", "S_perc", "dir", "det", "Q_cov"))
    for tag, m in rows:
        if m is None:
            print("%-18s  (missing)" % tag)
            continue
        dr = m.get("maneuver_direction_consistent")
        print("%-18s %7.3f %5s %5s %6s" % (
            tag, m.get("S_perc", 0.0),
            "-" if dr is None else ("%.0f" % dr),
            str(m.get("perception_detection_count")), str(m.get("Q_cov"))))


if __name__ == "__main__":
    main()
