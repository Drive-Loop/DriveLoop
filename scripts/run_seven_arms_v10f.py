"""Seven-arm motorcycle family under the final v10f protocol (T=4).

Arm -> baseline pairing extracted from the original v10b runs
(block 353/354 audit): ft arms read their ft-rendered baselines so the
evaluator's baseline subtraction uses matching weights; candidate70 has
a single baseline run (protocol-consistent with the v10b arms)."""
import glob, json, os, subprocess, sys

FT = ("/data/projects/DriveLoop/exp/drivedreamer2_img_cond_trainval_ft_local/"
      "models/checkpoint_epoch_1_step_6322/pytorch_gligen_weights.bin")
CASES = "experiments/manifests/v10_cases.json"

ARMS = [
    ("cl_v10f_c162_official",
     "outputs/driveloop/v10w_candidate162_baseline_official", {}),
    ("cl_v10f_c162_ft6322_dims",
     "outputs/driveloop/v10w_candidate162_baseline_ft6322",
     {"DRIVELOOP_DD2_WEIGHT_PATH": FT,
      "DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE": "1.5"}),
    ("cl_v10f_c2216_official",
     "outputs/driveloop/v10w_candidate2216_baseline_official", {}),
    ("cl_v10f_c2216_ft6322_dims",
     "outputs/driveloop/v10w_candidate2216_baseline_ft6322",
     {"DRIVELOOP_DD2_WEIGHT_PATH": FT,
      "DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE": "1.5"}),
    ("cl_v10f_c70_official",
     "outputs/driveloop/exp_c70_open_loop_baseline", {}),
    ("cl_v10f_c70_ft6322",
     "outputs/driveloop/exp_c70_open_loop_baseline",
     {"DRIVELOOP_DD2_WEIGHT_PATH": FT}),
    ("cl_v10f_c70_official_dims1p5",
     "outputs/driveloop/exp_c70_open_loop_baseline",
     {"DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE": "1.5"}),
]


def preflight():
    ok = True
    cases = json.load(open(CASES)).get("cases", [])
    print("CASES %d: %s" % (len(cases), [c.get("name") for c in cases]))
    if len(cases) != 5:
        ok = False
    print("FT_EXISTS", os.path.exists(FT))
    if not os.path.exists(FT):
        ok = False
    for tag, baseline, env in ARMS:
        has = bool(glob.glob(baseline + "/*/result.json")
                   or glob.glob(baseline + "/result.json"))
        print("%-28s baseline_ok=%s %s" % (tag, has, baseline))
        if not has:
            ok = False
    print("PREFLIGHT_OK" if ok else "PREFLIGHT_FAIL")
    return ok


def main():
    if os.environ.get("DRIVELOOP_SEVEN_PREFLIGHT") == "1":
        preflight()
        return
    for tag, baseline, arm_env in ARMS:
        out_dir = "outputs/driveloop/%s" % tag
        if glob.glob(out_dir + "/*/result.json"):
            print("SKIP_DONE", tag)
            continue
        env = dict(os.environ)
        env.update({"DRIVELOOP_EGO_INJECTION": "1", "DRIVELOOP_DD2_SEED_BANK": "0"})
        env.update(arm_env)
        cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
               "--source-from-baseline-dir", baseline,
               "--cases", CASES, "--output-dir", out_dir,
               "--max-iterations", "4", "--target-score", "0.99",
               "--perception-weights", "yolov8x.pt", "--use-task-utility"]
        print("RUN", tag)
        sys.stdout.flush()
        rc = subprocess.call(cmd, env=env)
        print("RC %s = %d" % (tag, rc))
        sys.stdout.flush()
    print("SEVEN_V10F_SUMMARY")
    print("%-28s %-26s %6s %6s %7s" % ("arm", "case", "open", "best", "delta"))
    grand = []
    for tag, baseline, arm_env in ARMS:
        deltas = []
        for rj in sorted(glob.glob("outputs/driveloop/%s/*/result.json" % tag)):
            res = json.load(open(rj))
            ah = res.get("attempt_history") or []
            a0 = 0.0
            if ah:
                a0 = float((((ah[0].get("evaluation") or {}).get("metrics"))
                            or {}).get("S_perc") or 0.0)
            best = float((((res.get("best_evaluation") or {}).get("metrics"))
                          or {}).get("S_perc") or 0.0)
            deltas.append(best - a0)
            print("%-28s %-26s %6.3f %6.3f %+7.3f" % (
                tag, rj.split("/")[3], a0, best, best - a0))
        if deltas:
            m = sum(deltas) / len(deltas)
            grand.append(m)
            print("%-28s %-26s %6s %6s %+7.3f  (arm mean)" % (tag, "", "", "", m))
    if grand:
        print("GRAND_MEAN %+0.4f over %d arms" % (sum(grand) / len(grand), len(grand)))


if __name__ == "__main__":
    main()
