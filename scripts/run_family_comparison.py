"""Best-of-4 and text-only baselines on the seven-arm motorcycle
family, matching the v10f arm/baseline/env pairing. Summary compares
open (v10f attempt 0), best-of-4 (a0 + plain banks 6/7/8), text-only
loop (T=4, DRIVELOOP_TEXT_ONLY_REFINER=1), and DriveLoop (v10f best)
per arm and overall."""
import glob, json, os, subprocess, sys

from scripts.run_seven_arms_v10f import ARMS, CASES

BANKS = [6, 7, 8]


def sperc(m):
    return float((m or {}).get("S_perc") or 0.0)


def best_m(res):
    return ((res.get("best_evaluation") or {}).get("metrics")) or {}


def a0_m(res):
    ah = res.get("attempt_history") or []
    return (((ah[0] if ah else {}).get("evaluation") or {}).get("metrics")) or {}


def render(tag, baseline, env_extra, out_dir, iters, extra_env):
    env = dict(os.environ)
    env.update({"DRIVELOOP_EGO_INJECTION": "1"})
    env.update(env_extra)
    env.update(extra_env)
    cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
           "--source-from-baseline-dir", baseline, "--cases", CASES,
           "--output-dir", out_dir, "--max-iterations", str(iters),
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
        for bank in BANKS:
            out = "outputs/driveloop/cl_bo4_%s_bank%d" % (short, bank)
            if glob.glob(out + "/*/result.json"):
                print("SKIP_DONE", out)
                continue
            render(tag, baseline, arm_env, out, 1,
                   {"DRIVELOOP_DD2_SEED_BANK": str(bank)})
        out = "outputs/driveloop/cl_text_%s" % short
        if glob.glob(out + "/*/result.json"):
            print("SKIP_DONE", out)
        else:
            render(tag, baseline, arm_env, out, 4,
                   {"DRIVELOOP_DD2_SEED_BANK": "0",
                    "DRIVELOOP_TEXT_ONLY_REFINER": "1"})
    print("FAMILY_COMPARISON_SUMMARY")
    print("%-24s %7s %7s %7s %7s" % ("arm", "open", "bo4", "text", "ours"))
    grand = [0.0, 0.0, 0.0, 0.0]
    n_arms = 0
    wins = [0, 0, 0]
    total_cases = 0
    for tag, baseline, arm_env in ARMS:
        short = tag.replace("cl_v10f_", "")
        sums = [0.0, 0.0, 0.0, 0.0]
        cases = sorted(glob.glob("outputs/driveloop/%s/*/result.json" % tag))
        for rj in cases:
            case = rj.split("/")[3]
            res = json.load(open(rj))
            a0 = sperc(a0_m(res))
            ours = sperc(best_m(res))
            bo4 = a0
            for bank in BANKS:
                g = glob.glob("outputs/driveloop/cl_bo4_%s_bank%d/%s/result.json"
                              % (short, bank, case))
                if g:
                    bo4 = max(bo4, sperc(best_m(json.load(open(g[0])))))
            text = 0.0
            g = glob.glob("outputs/driveloop/cl_text_%s/%s/result.json"
                          % (short, case))
            if g:
                text = sperc(best_m(json.load(open(g[0]))))
            for i, v in enumerate((a0, bo4, text, ours)):
                sums[i] += v
            total_cases += 1
            if ours > bo4:
                wins[0] += 1
            elif ours == bo4:
                wins[1] += 1
            else:
                wins[2] += 1
        k = max(len(cases), 1)
        means = [s / k for s in sums]
        for i in range(4):
            grand[i] += means[i]
        n_arms += 1
        print("%-24s %7.3f %7.3f %7.3f %7.3f" % (short, *means))
    print("%-24s %7.3f %7.3f %7.3f %7.3f  (grand mean)" % (
        "GRAND", *[g / max(n_arms, 1) for g in grand]))
    print("ours vs bo4 over %d cases: win %d / tie %d / loss %d" % (
        total_cases, wins[0], wins[1], wins[2]))


if __name__ == "__main__":
    main()
