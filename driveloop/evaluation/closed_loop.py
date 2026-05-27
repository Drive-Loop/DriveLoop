import copy
import datetime
import json
import os
import traceback

from termcolor import colored

from chatsim.agents.prompt_refine_agent import PromptRefineAgent
from chatsim.agents.utils import check_and_mkdirs, sanitize_filename
from chatsim.baselines import build_generation_backend
from chatsim.evaluation.evaluator import build_evaluator


class ClosedLoopController:
    """Run ChatSim, evaluate the video, and refine prompts until passing."""

    def __init__(self, chatsim_cls, base_config, args):
        self.chatsim_cls = chatsim_cls
        self.base_config = copy.deepcopy(base_config)
        self.args = args
        self.evaluator = build_evaluator(args)
        self.generation_backend = build_generation_backend(chatsim_cls, self.base_config, args)
        self.refine_agent = PromptRefineAgent(model=args.refiner_model)
        self.attempt_history = []
        self.prompt_raw = getattr(args, "prompt_raw", args.prompt)
        self.semantic_prompt = getattr(args, "prompt_semantic", args.prompt)
        self.original_prompt = self.prompt_raw
        self.requested_long_tail_tags = list(getattr(args, "requested_long_tail_tags", []))
        self.prompt_conditioning = getattr(args, "prompt_conditioning", None)
        self.long_tail_plan = getattr(args, "long_tail_plan", None)
        self.long_tail_controller = getattr(args, "long_tail_controller", None)

        check_and_mkdirs(args.evaluation_output_dir)
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        manifest_name = sanitize_filename(args.simulation_name, default="closed_loop")
        self.manifest_path = os.path.join(
            args.evaluation_output_dir,
            f"{manifest_name}_closed_loop_{timestamp}.json",
        )

    def run(self):
        semantic_prompt = self.semantic_prompt
        best_attempt = None

        for attempt_idx in range(self.args.max_attempts):
            attempt_id = attempt_idx + 1
            render_prompt, current_long_tail_plan = self._prepare_render_prompt(semantic_prompt)
            self.semantic_prompt = semantic_prompt
            self.long_tail_plan = current_long_tail_plan
            print(
                f"{colored('[Closed Loop]', color='cyan', attrs=['bold'])} "
                f"Attempt {attempt_id}/{self.args.max_attempts}"
            )
            print(f"{colored('[Closed Loop Prompt]', color='cyan', attrs=['bold'])} {render_prompt}\n")

            try:
                video_path, logging_name = self._render_one_attempt(
                    render_prompt,
                    current_long_tail_plan,
                    attempt_id,
                )
                evaluation = self.evaluator.evaluate(
                    video_path=video_path,
                    prompt=render_prompt,
                    metadata={
                        "attempt_id": attempt_id,
                        "generation_backend": self.args.generation_backend,
                        "original_prompt": self.original_prompt,
                        "raw_prompt": self.prompt_raw,
                        "semantic_prompt": semantic_prompt,
                        "prompt": render_prompt,
                        "video_path": video_path,
                        "logging_name": logging_name,
                        "target_score": self.args.target_score,
                        "long_tail_plan": (
                            current_long_tail_plan.to_dict() if current_long_tail_plan else None
                        ),
                    },
                )
                attempt_record = {
                    "attempt_id": attempt_id,
                    "generation_backend": self.args.generation_backend,
                    "semantic_prompt": semantic_prompt,
                    "prompt": render_prompt,
                    "video_path": video_path,
                    "logging_name": logging_name,
                    "long_tail_plan": (
                        current_long_tail_plan.to_dict() if current_long_tail_plan else None
                    ),
                    "evaluation": evaluation.to_dict(),
                }
                self.attempt_history.append(attempt_record)
                best_attempt = self._select_best(best_attempt, attempt_record)
                self._write_manifest(best_attempt, status="running")

                print(
                    f"{colored('[Closed Loop Evaluation]', color='cyan', attrs=['bold'])} "
                    f"score={evaluation.score:.4f}, threshold={evaluation.threshold:.4f}, "
                    f"passed={evaluation.passed}\n"
                )

                if evaluation.passed:
                    self._write_manifest(best_attempt, status="passed")
                    return attempt_record

                if attempt_id == self.args.max_attempts:
                    break

                refinement = self.refine_agent.refine_prompt(
                    original_prompt=self.original_prompt,
                    current_prompt=semantic_prompt,
                    evaluation_result=evaluation,
                    attempt_history=self.attempt_history,
                )
                attempt_record["refinement"] = refinement
                semantic_prompt = refinement["refined_prompt"]
                self._write_manifest(best_attempt, status="running")

            except Exception as e:
                error_record = {
                    "attempt_id": attempt_id,
                    "semantic_prompt": semantic_prompt,
                    "prompt": render_prompt,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
                self.attempt_history.append(error_record)
                self._write_manifest(best_attempt, status="failed")
                raise

        self._write_manifest(best_attempt, status="not_passed")
        return best_attempt

    def _render_one_attempt(self, render_prompt, long_tail_plan, attempt_id):
        result = self.generation_backend.render(render_prompt, attempt_id=attempt_id)
        video_path = result.video_path
        if self.long_tail_controller is not None and long_tail_plan is not None:
            video_path = self.long_tail_controller.apply_postprocess(
                video_path,
                long_tail_plan,
                attempt_id=attempt_id,
            )
        return video_path, result.logging_name

    def _prepare_render_prompt(self, semantic_prompt):
        if self.long_tail_controller is None:
            return semantic_prompt, None
        long_tail_plan = self.long_tail_controller.build_plan(
            prompt=semantic_prompt,
            requested_tags=self.requested_long_tail_tags,
        )
        render_prompt = self.long_tail_controller.augment_prompt(semantic_prompt, long_tail_plan)
        return render_prompt, long_tail_plan

    def _select_best(self, best_attempt, attempt_record):
        if best_attempt is None:
            return attempt_record
        best_score = best_attempt.get("evaluation", {}).get("score", float("-inf"))
        score = attempt_record.get("evaluation", {}).get("score", float("-inf"))
        return attempt_record if score > best_score else best_attempt

    def _write_manifest(self, best_attempt, status):
        payload = {
            "status": status,
            "generation_backend": self.args.generation_backend,
            "raw_prompt": self.prompt_raw,
            "original_prompt": self.original_prompt,
            "semantic_prompt": self.semantic_prompt,
            "requested_long_tail_tags": self.requested_long_tail_tags,
            "target_score": self.args.target_score,
            "max_attempts": self.args.max_attempts,
            "best_attempt": best_attempt,
            "attempts": self.attempt_history,
        }
        if self.prompt_conditioning is not None:
            payload["prompt_conditioning"] = self.prompt_conditioning.to_dict()
        if self.long_tail_plan is not None:
            payload["long_tail_plan"] = self.long_tail_plan.to_dict()
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
