import argparse
import copy
import json
import os
import pprint

import imageio.v2 as imageio
import openai
from termcolor import colored
from driveloop.evaluation.closed_loop import ClosedLoopController
from driveloop.agents.asset_select_agent import AssetSelectAgent
from driveloop.agents.background_rendering_agent import BackgroundRenderingAgent
from driveloop.agents.background_rendering_3dgs_agent import BackgroundRendering3DGSAgent
from driveloop.agents.deletion_agent import DeletionAgent
from driveloop.agents.foreground_rendering_agent import ForegroundRenderingAgent
from driveloop.agents.motion_agent import MotionAgent
from driveloop.agents.project_manager import ProjectManager
from driveloop.agents.view_adjust_agent import ViewAdjustAgent
from driveloop.agents.utils import check_and_mkdirs, generate_video, read_yaml, sanitize_filename
from driveloop.baselines import build_generation_backend
from driveloop.conditioning import LongTailScenarioController, MicrophoneRecorder, MultimodalConditioner
from driveloop.scene import Scene

def get_parser():
    parser = argparse.ArgumentParser(description="ChatSim argrument parser.")
    parser.add_argument(
        "--config_yaml", "-y", type=str,
        default="config/waymo-1287.yaml",
        help="path to config file",
    )
    parser.add_argument(
        "--prompt", "-p", type=str,
        default="add a straight driving car in the scene",
        help="language prompt to ChatSim.",
    )
    parser.add_argument(
        "--audio_prompt_paths", nargs="*", default=None,
        help="optional audio instructions to transcribe and merge into the prompt.",
    )
    parser.add_argument(
        "--record_audio_prompt", action="store_true",
        help="record a new microphone instruction before generation and merge it into the prompt.",
    )
    parser.add_argument(
        "--record_audio_duration_sec", type=float, default=None,
        help="optional microphone recording duration in seconds. If omitted, recording stops when you press Enter.",
    )
    parser.add_argument(
        "--record_audio_device", type=str, default=None,
        help="optional microphone device override passed to the ffmpeg recording backend.",
    )
    parser.add_argument(
        "--record_audio_backend", type=str, default="auto",
        choices=["auto", "ffmpeg"],
        help="microphone recording backend for direct voice input.",
    )
    parser.add_argument(
        "--record_audio_output_path", type=str, default=None,
        help="optional path for the recorded microphone prompt WAV file.",
    )
    parser.add_argument(
        "--reference_image_paths", nargs="*", default=None,
        help="optional reference images for multimodal prompt grounding.",
    )
    parser.add_argument(
        "--reference_video_paths", nargs="*", default=None,
        help="optional reference videos for multimodal prompt grounding.",
    )
    parser.add_argument(
        "--reference_sketch_paths", nargs="*", default=None,
        help="optional sketch images for multimodal prompt grounding.",
    )
    parser.add_argument(
        "--conditioning_caption_model", type=str, default="Salesforce/blip-image-captioning-base",
        help="caption model used for multimodal image, sketch, and video grounding.",
    )
    parser.add_argument(
        "--conditioning_fusion_model", type=str, default="gpt-4",
        help="chat model used to fuse multimodal references into a single prompt.",
    )
    parser.add_argument(
        "--conditioning_video_frames", type=int, default=4,
        help="number of reference video frames sampled for multimodal grounding.",
    )
    parser.add_argument(
        "--conditioning_report_dir", type=str, default="results/conditioning",
        help="directory for multimodal conditioning and long-tail planning reports.",
    )
    parser.add_argument(
        "--long_tail_scenarios", type=str, default="",
        help="comma-separated long-tail tags such as animal_crossing,traffic_accident,heavy_rain,fog,snow.",
    )
    parser.add_argument(
        "--weather_strength", type=float, default=0.45,
        help="strength of long-tail weather post-processing effects.",
    )
    parser.add_argument(
        "--simulation_name", "-s", type=str,
        default="demo",
        help="simulation experiment name.",
    )
    parser.add_argument(
        "--closed_loop", action="store_true",
        help="enable evaluator-guided prompt refinement loop.",
    )
    parser.add_argument(
        "--max_attempts", type=int, default=3,
        help="maximum number of render/evaluate/refine attempts in closed-loop mode.",
    )
    parser.add_argument(
        "--target_score", type=float, default=0.8,
        help="minimum evaluator score required to stop the closed loop.",
    )
    parser.add_argument(
        "--evaluator_type", type=str, default="shell",
        choices=["shell", "python", "json", "perception"],
        help="autonomous-driving evaluator adapter.",
    )
    parser.add_argument(
        "--evaluator_command", type=str, default=None,
        help="shell evaluator command template. Supports {video_path}, {prompt}, {attempt_id}, {output_json}, {metadata_json}.",
    )
    parser.add_argument(
        "--evaluator_python", type=str, default=None,
        help="python evaluator callable in module:function format.",
    )
    parser.add_argument(
        "--evaluator_json", type=str, default=None,
        help="precomputed evaluator JSON file for offline debugging.",
    )
    parser.add_argument(
        "--evaluator_score_key", type=str, default="score",
        help="JSON key used as evaluation score.",
    )
    parser.add_argument(
        "--evaluator_pass_key", type=str, default="passed",
        help="JSON key used as pass/fail flag. If absent, score >= target_score is used.",
    )
    parser.add_argument(
        "--evaluator_timeout_sec", type=int, default=3600,
        help="timeout for shell evaluator command.",
    )
    parser.add_argument(
        "--evaluation_output_dir", type=str, default="results/evaluations",
        help="directory for closed-loop evaluation manifests and evaluator outputs.",
    )
    parser.add_argument(
        "--perception_model", type=str, default="yolo11m.pt",
        help="YOLO model for --evaluator_type perception.",
    )
    parser.add_argument(
        "--perception_tracker", type=str, default="botsort.yaml",
        help="Ultralytics tracker config for --evaluator_type perception.",
    )
    parser.add_argument(
        "--perception_classes", type=str, default="0,1,2,3,5,7,9,11",
        help="comma-separated COCO class IDs for perception evaluation, or 'all'.",
    )
    parser.add_argument(
        "--perception_conf", type=float, default=0.25,
        help="YOLO confidence threshold for perception evaluation.",
    )
    parser.add_argument(
        "--perception_iou", type=float, default=0.50,
        help="YOLO NMS IoU threshold for perception evaluation.",
    )
    parser.add_argument(
        "--perception_imgsz", type=int, default=1280,
        help="YOLO inference image size for perception evaluation.",
    )
    parser.add_argument(
        "--perception_device", type=str, default=None,
        help="YOLO device such as '0', 'cpu', or 'cuda:0'.",
    )
    parser.add_argument(
        "--refiner_model", type=str, default="gpt-4",
        help="OpenAI chat model used by the prompt refinement agent.",
    )
    parser.add_argument(
        "--generation_backend", type=str, default="native_chatsim",
        choices=[
            "native_chatsim",
            "magicdrive_v2",
        ],
        help="video generation backend. Use magicdrive_v2 to run the MagicDrive-V2 baseline.",
    )
    parser.add_argument(
        "--backend_command", type=str, default=None,
        help=(
            "shell command template for the MagicDrive-V2 baseline. Supports "
            "{prompt}, {attempt_id}, {simulation_name}, {video_path}, "
            "{output_json}, {metadata_json}, {config_yaml}, {backend_name}."
        ),
    )
    parser.add_argument(
        "--backend_workdir", type=str, default=None,
        help="optional working directory for the MagicDrive-V2 baseline command.",
    )
    parser.add_argument(
        "--backend_output_dir", type=str, default="results/baselines",
        help="directory for MagicDrive-V2 baseline videos and manifests.",
    )
    parser.add_argument(
        "--backend_timeout_sec", type=int, default=7200,
        help="timeout for the MagicDrive-V2 baseline generation command.",
    )
    return parser


def parse_args(argv=None):
    return get_parser().parse_args(argv)


def _prepare_conditioned_prompt(args):
    _maybe_record_audio_prompt(args)
    multimodal_conditioner = MultimodalConditioner(
        caption_model=args.conditioning_caption_model,
        fusion_model=args.conditioning_fusion_model,
        max_video_frames=args.conditioning_video_frames,
    )
    conditioning_result = multimodal_conditioner.prepare_prompt(
        raw_prompt=args.prompt,
        audio_paths=args.audio_prompt_paths,
        image_paths=args.reference_image_paths,
        video_paths=args.reference_video_paths,
        sketch_paths=args.reference_sketch_paths,
    )

    requested_long_tail_tags = [
        item.strip() for item in str(args.long_tail_scenarios or "").split(",") if item.strip()
    ]
    long_tail_controller = LongTailScenarioController(
        output_dir=args.conditioning_report_dir,
        weather_strength=args.weather_strength,
    )
    long_tail_plan = long_tail_controller.build_plan(
        prompt=conditioning_result.fused_prompt,
        requested_tags=requested_long_tail_tags,
    )
    final_prompt = long_tail_controller.augment_prompt(conditioning_result.fused_prompt, long_tail_plan)

    args.prompt_raw = args.prompt
    args.prompt_semantic = conditioning_result.fused_prompt
    args.requested_long_tail_tags = requested_long_tail_tags
    args.prompt = final_prompt
    args.prompt_conditioning = conditioning_result
    args.long_tail_controller = long_tail_controller
    args.long_tail_plan = long_tail_plan
    _write_conditioning_report(args, conditioning_result, long_tail_plan, final_prompt)


def _write_conditioning_report(args, conditioning_result, long_tail_plan, final_prompt):
    check_and_mkdirs(args.conditioning_report_dir)
    stem = sanitize_filename(args.simulation_name, default="conditioning")
    report_path = os.path.join(args.conditioning_report_dir, f"{stem}_conditioning.json")
    payload = {
        "raw_prompt": getattr(args, "prompt_raw", args.prompt),
        "final_prompt": final_prompt,
        "recorded_audio_prompt_path": getattr(args, "recorded_audio_prompt_path", None),
        "multimodal_conditioning": conditioning_result.to_dict(),
        "long_tail_plan": long_tail_plan.to_dict(),
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _maybe_record_audio_prompt(args):
    if not getattr(args, "record_audio_prompt", False):
        return

    recorder = MicrophoneRecorder(
        output_dir=os.path.join(args.conditioning_report_dir, "recorded_audio_prompts"),
    )
    recorded = recorder.record(
        simulation_name=args.simulation_name,
        duration_sec=args.record_audio_duration_sec,
        device=args.record_audio_device,
        backend=args.record_audio_backend,
        output_path=args.record_audio_output_path,
    )

    audio_prompt_paths = list(args.audio_prompt_paths or [])
    audio_prompt_paths.append(recorded.path)
    args.audio_prompt_paths = audio_prompt_paths
    args.recorded_audio_prompt_path = recorded.path


def _postprocess_video_if_needed(args, video_path, attempt_id=None):
    controller = getattr(args, "long_tail_controller", None)
    plan = getattr(args, "long_tail_plan", None)
    if controller is None or plan is None:
        return video_path
    return controller.apply_postprocess(video_path, plan, attempt_id=attempt_id)


class ChatSim:
    def __init__(self, config):
        self.config = config

        self.scene = Scene(config["scene"])  # agents share and maintain the same scene

        agents_config = config['agents']
        self.project_manager = ProjectManager(agents_config["project_manager"])
        self.asset_select_agent = AssetSelectAgent(agents_config["asset_select_agent"])
        self.deletion_agent = DeletionAgent(agents_config["deletion_agent"])
        self.foreground_rendering_agent = ForegroundRenderingAgent(agents_config["foreground_rendering_agent"])
        self.motion_agent = MotionAgent(agents_config["motion_agent"])
        self.view_adjust_agent = ViewAdjustAgent(agents_config["view_adjust_agent"])
        # we can choose between nerf and 3dgs for background rendering
        if agents_config['background_rendering_agent'].get("scene_representation", 'nerf') == 'nerf':
            self.background_rendering_agent = BackgroundRenderingAgent(agents_config["background_rendering_agent"])
        else:
            self.background_rendering_agent = BackgroundRendering3DGSAgent(agents_config["background_rendering_agent"])

        self.tech_agents = {
            "asset_select_agent": self.asset_select_agent,
            "background_rendering_agent": self.background_rendering_agent,
            "deletion_agent": self.deletion_agent,
            "foreground_rendering_agent": self.foreground_rendering_agent,
            "motion_agent": self.motion_agent,
            "view_adjust_agent": self.view_adjust_agent,
        }

        self.current_prompt = (
            "An empty prompt"  # initialization place holder for debugging
        )

    def setup_init_frame(self):
        """Setup initial frame for ChatSim's reasoning and rendering.
        """
        if not os.path.exists(self.scene.init_img_path):
            print(f"{colored('[Note]', color='red', attrs=['bold'])} ",
                  f"{colored('can not find init image, rendering it for the first time')}\n")
            # it will update scene.current_images
            self.background_rendering_agent.func_render_background(self.scene)
            # save the initial image
            imageio.imwrite(self.scene.init_img_path, self.scene.current_images[0])
        else:
            self.scene.current_images = [imageio.imread(self.scene.init_img_path)] * self.scene.frames


    def execute_llms(self, prompt):
        """Entry of ChatSim's reasoning.
        We perform multi-LLM reasoning for the user's prompt

        Input:
            prompt : str
                language prompt to ChatSim.
        """
        self.scene.setup_cars()
        self.current_prompt = prompt

        # execute agent's LLM part
        tasks = self.project_manager.decompose_prompt(self.scene, prompt)

        for task in tasks.values():
            print(
                f"{colored('[Performing Single Prompt]', on_color='on_blue', attrs=['bold'])} {colored(task, attrs=['bold'])}\n"
            )
            self.project_manager.dispatch_task(self.scene, task, self.tech_agents)

        print(colored("scene.added_cars_dict", color="red", attrs=["bold"]), end=' ')
        pprint.pprint(self.scene.added_cars_dict.keys())
        print(colored("scene.removed_cars", color="red", attrs=["bold"]), end=' ')
        pprint.pprint(self.scene.removed_cars)

    def execute_funcs(self):
        """Entry of ChatSim's rendering functions
        We perform agent's functions following the self.scene's configuration.
        self.scene's configuration are updated in self.execute_llms()
        """
        # use scene.current_extrinsics, render (novel) view images
        self.background_rendering_agent.func_render_background(self.scene)

        # Inpaint. 
        self.deletion_agent.func_inpaint_scene(self.scene)

        # Retrieve blender file from asset bank
        self.asset_select_agent.func_retrieve_blender_file(self.scene)

        # Blender add car. If no addition, just return
        self.foreground_rendering_agent.func_blender_add_cars(self.scene)

        # Generate Video
        return generate_video(self.scene, self.current_prompt)


def run_pipeline(args):
    _prepare_conditioned_prompt(args)

    config = read_yaml(args.config_yaml)
    config['scene']["simulation_name"] = args.simulation_name

    if args.closed_loop:
        controller = ClosedLoopController(ChatSim, config, args)
        attempt_record = controller.run()
        if attempt_record is None:
            return {
                "mode": "closed_loop",
                "video_path": None,
                "attempt_record": None,
                "manifest_path": controller.manifest_path,
                "prompt_raw": getattr(args, "prompt_raw", args.prompt),
                "prompt_semantic": getattr(args, "prompt_semantic", args.prompt),
                "prompt_render": args.prompt,
                "prompt_conditioning": (
                    args.prompt_conditioning.to_dict() if getattr(args, "prompt_conditioning", None) else None
                ),
                "long_tail_plan": (
                    args.long_tail_plan.to_dict() if getattr(args, "long_tail_plan", None) else None
                ),
            }
        return {
            "mode": "closed_loop",
            "video_path": attempt_record.get("video_path"),
            "attempt_record": attempt_record,
            "manifest_path": controller.manifest_path,
            "prompt_raw": getattr(args, "prompt_raw", args.prompt),
            "prompt_semantic": getattr(args, "prompt_semantic", args.prompt),
            "prompt_render": attempt_record.get("prompt", args.prompt),
            "prompt_conditioning": (
                args.prompt_conditioning.to_dict() if getattr(args, "prompt_conditioning", None) else None
            ),
            "long_tail_plan": (
                args.long_tail_plan.to_dict() if getattr(args, "long_tail_plan", None) else None
            ),
        }

    backend = build_generation_backend(ChatSim, config, args)
    result = backend.render(args.prompt, attempt_id=1)
    video_path = _postprocess_video_if_needed(args, result.video_path, attempt_id=1)
    return {
        "mode": "single_pass",
        "video_path": video_path,
        "generation_result": result.to_dict(),
        "prompt_raw": getattr(args, "prompt_raw", args.prompt),
        "prompt_semantic": getattr(args, "prompt_semantic", args.prompt),
        "prompt_render": args.prompt,
        "prompt_conditioning": (
            args.prompt_conditioning.to_dict() if getattr(args, "prompt_conditioning", None) else None
        ),
        "long_tail_plan": (
            args.long_tail_plan.to_dict() if getattr(args, "long_tail_plan", None) else None
        ),
    }


def make_args(overrides=None):
    parser = get_parser()
    args = parser.parse_args([])
    for key, value in (overrides or {}).items():
        setattr(args, key, value)
    return args


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args)
