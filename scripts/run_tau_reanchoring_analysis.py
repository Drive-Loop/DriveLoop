from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from driveloop.tau_reanchoring import build_tau_reanchoring, render_markdown


def parse_arm(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"--arm expects name=path, got: {value}")
    name, _, path = value.partition("=")
    if not name or not path:
        raise argparse.ArgumentTypeError(f"--arm expects name=path, got: {value}")
    return name, Path(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Transparent tau re-anchoring from experiment arm J distributions "
            "(anchored on the open-loop arm; see driveloop/tau_reanchoring.py)."
        )
    )
    parser.add_argument(
        "--arm", action="append", required=True, type=parse_arm, metavar="NAME=DIR",
        help="experiment arm output dir (repeatable), e.g. open_loop=outputs/driveloop/exp_v8_open_loop",
    )
    parser.add_argument("--anchor-arm", default="open_loop")
    parser.add_argument("--current-tau", type=float, default=0.7)
    parser.add_argument("--primary-rule", default="anchor_mean_plus_1_std")
    parser.add_argument(
        "--capability-configuration", default=None,
        help="free-form label, e.g. candidate70_mini_ckpt_8f",
    )
    parser.add_argument("--output", type=Path, default=None, help="JSON manifest path")
    parser.add_argument("--markdown-output", type=Path, default=None)
    args = parser.parse_args(argv)

    arm_dirs = dict(args.arm)
    if len(arm_dirs) != len(args.arm):
        parser.error("duplicate arm names in --arm")

    manifest = build_tau_reanchoring(
        arm_dirs=arm_dirs,
        anchor_arm=args.anchor_arm,
        current_tau=args.current_tau,
        primary_rule=args.primary_rule,
        capability_configuration=args.capability_configuration,
    )
    markdown = render_markdown(manifest)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown, encoding="utf-8")

    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
