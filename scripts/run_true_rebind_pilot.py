"""True-rebinding pilot on the candidate1677 margin subset.

Per offset in {0,1,2}: render the no-injection baseline of THAT window
(honest baseline subtraction), then a single-pass REAL-path probe at
the attempt-0 recipe with condition source_rebinding. Reports the
bound front frame per offset (the proof of a real shift), S_perc, and
the injection path."""
import glob, json, os, subprocess, sys

REPORT = ("/mnt/driveloop_full/processed/nuscenes/v1.0-trainval/"
          "candidate1677_source_bound_m1/cam_all_train/v0.0.1/subset_report.json")
DS = ("/mnt/driveloop_full/processed/nuscenes/v1.0-trainval/"
      "candidate1677_source_bound_m1/cam_all_train/v0.0.1")


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
    rep = json.load(open(REPORT))
    ids = ((rep.get("source_binding") or {}).get("selector") or {}).get(
        "identity_summary_path")
    base_case = json.load(open("experiments/manifests/v10_baseline.json"))["cases"][0]
    probe_case = json.load(open("experiments/manifests/v10_truck.json"))["cases"][0]
    for off in (0, 1, 2):
        bl_dir = "outputs/driveloop/candidate1677_baseline_m1_off%d" % off
        if not glob.glob(bl_dir + "/*/result.json"):
            man = "/tmp/bl_m1_off%d.json" % off
            json.dump({"cases": [{
                "name": "%s_off%d" % (base_case["name"], off),
                "prompt": base_case["prompt"],
                "condition": {"source_rebinding": {"candidate_offset": off,
                                                   "reason": "true_rebind_pilot"}},
            }]}, open(man, "w"))
            env = dict(os.environ)
            env["DRIVELOOP_DD2_SEED_BANK"] = "0"
            cmd = [sys.executable, "-u", "-m", "scripts.run_driveloop_experiment",
                   "--cases", man, "--output-dir", bl_dir,
                   "--backend", "drivedreamer2",
                   "--config-name", "drivedreamer2_img_cond_mini_local",
                   "--source-candidate-id", "candidate1677",
                   "--source-identity-summary", ids,
                   "--baseline-dataset-dir", DS,
                   "--max-iterations", "1", "--target-score", "0.99"]
            print("RUN baseline off%d" % off); sys.stdout.flush()
            rc = subprocess.call(cmd, env=env)
            print("RC baseline off%d = %d" % (off, rc)); sys.stdout.flush()
        else:
            print("SKIP_DONE baseline off%d" % off)
    for off in (0, 1, 2):
        out_dir = "outputs/driveloop/candidate1677_rebind_real_off%d" % off
        if glob.glob(out_dir + "/*/result.json"):
            print("SKIP_DONE probe off%d" % off)
            continue
        man = "/tmp/probe_m1_off%d.json" % off
        json.dump({"cases": [{
            "name": "%s_off%d" % (probe_case["name"], off),
            "prompt": probe_case["prompt"],
            "condition": {"source_rebinding": {"candidate_offset": off,
                                               "reason": "true_rebind_pilot"}},
        }]}, open(man, "w"))
        env = dict(os.environ)
        env.update({"DRIVELOOP_EGO_INJECTION": "1", "DRIVELOOP_DD2_SEED_BANK": "0"})
        cmd = [sys.executable, "-u", "-m", "scripts.render_window_case",
               "--source-from-baseline-dir",
               "outputs/driveloop/candidate1677_baseline_m1_off%d" % off,
               "--cases", man, "--output-dir", out_dir,
               "--max-iterations", "1", "--target-score", "0.99",
               "--perception-weights", "yolov8x.pt", "--use-task-utility"]
        print("RUN probe off%d" % off); sys.stdout.flush()
        rc = subprocess.call(cmd, env=env)
        print("RC probe off%d = %d" % (off, rc)); sys.stdout.flush()
    print("REBIND_PILOT_SUMMARY")
    print("%4s %6s %6s %7s %5s %5s %-6s %s" % (
        "off", "skip", "fidx", "S_perc", "dir", "det", "path", "fallback"))
    for off in (0, 1, 2):
        g = glob.glob("outputs/driveloop/candidate1677_rebind_real_off%d/*/result.json" % off)
        if not g:
            print("%4d  (missing)" % off)
            continue
        res = json.load(open(g[0]))
        binds, maps = [], []
        fk(res, "dd2_source_sample_binding", binds)
        fk(res, "actor_motion_frame_mapping", maps)
        b = binds[0] if binds else {}
        fr = b.get("front_record") or {}
        m = ((res.get("best_evaluation") or {}).get("metrics")) or {}
        mode = maps[0].get("mode") if maps else None
        short = {"source_bound_real_track_ego": "REAL",
                 "ego_frame_one_entry_per_video_frame": "SYN"}.get(mode, "?")
        fb = maps[0].get("real_track_fallback_reason") if maps else None
        dr = m.get("maneuver_direction_consistent")
        print("%4d %6s %6s %7.3f %5s %5s %-6s %s" % (
            off, b.get("dd2_batch_skip"), fr.get("frame_idx"),
            float(m.get("S_perc") or 0.0),
            "-" if dr is None else ("%.0f" % dr),
            str(m.get("perception_detection_count")), short, fb))


if __name__ == "__main__":
    main()
