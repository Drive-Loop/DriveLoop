# ChatSim Closed-Loop Evaluation

This extension keeps the original ChatSim flow unchanged:

```text
user prompt -> ChatSim agents -> rendered video
```

It adds an outer loop:

```text
rendered video -> autonomous-driving evaluator -> score/feedback -> prompt refinement -> rerender
```

The evaluator can be either a built-in perception evaluator or a custom plug-in because different autonomous-driving algorithms expose different interfaces.

## MagicDrive-V2 Baseline

The project now supports two generation modes:

```text
native_chatsim
magicdrive_v2
```

The MagicDrive-V2 baseline is executed through a shell command template. The project does not reimplement MagicDrive-V2 internally. Instead, it provides a unified experiment harness so that the same prompt-conditioning, long-tail control, evaluator, and closed-loop logging can be reused across ChatSim and MagicDrive-V2.

Example with MagicDrive-V2:

```bash
python main.py \
  -y config/3dgs-waymo-1137.yaml \
  -p "Add a clear red car in the front lane, driving away smoothly." \
  -s magicdrive_baseline \
  --generation_backend magicdrive_v2 \
  --backend_workdir /path/to/MagicDrive-V2 \
  --backend_command "python infer.py --prompt {prompt} --output_video {video_path}"
```

Supported backend placeholders:

- `{prompt}`
- `{attempt_id}`
- `{simulation_name}`
- `{video_path}`
- `{output_json}`
- `{metadata_json}`
- `{config_yaml}`
- `{backend_name}`

An external backend may either:

- write its video directly to `{video_path}`, or
- write a JSON file to `{output_json}` containing at least `"video_path": "..."`

This makes it possible to compare ChatSim and MagicDrive-V2 under the same evaluation pipeline.

## Evaluator JSON Contract

Every evaluator should return JSON with at least:

```json
{
  "score": 0.72,
  "passed": false,
  "summary": "The ego vehicle failed to keep enough distance.",
  "failure_reasons": ["The inserted car is too close to the ego lane."],
  "suggestions": ["Move the inserted vehicle farther forward and make motion smoother."],
  "metrics": {
    "collision_rate": 0.1,
    "min_ttc": 0.8
  }
}
```

If `passed` is omitted, ChatSim uses `score >= --target_score`.

## Shell Evaluator

The shell command may write JSON to `{output_json}` or print JSON to stdout.

```bash
python main.py \
  -y config/3dgs-waymo-1137.yaml \
  -p "Add a Benz G in front of me, driving away fast." \
  -s closed_loop_demo \
  --closed_loop \
  --max_attempts 3 \
  --target_score 0.8 \
  --evaluator_type shell \
  --evaluator_command "python /path/to/evaluate.py --video {video_path} --out {output_json}"
```

Available command placeholders:

- `{video_path}`
- `{prompt}`
- `{attempt_id}`
- `{output_json}`
- `{metadata_json}`

## Built-In Perception Evaluator

Use this evaluator when the target benchmark is perception quality: object detection stability, tracking stability, confidence, ID switches, and robustness to short occlusion.

The built-in evaluator runs YOLO11 detection with BoT-SORT tracking through Ultralytics:

```bash
python main.py \
  -y config/3dgs-waymo-1137.yaml \
  -p "Add a Benz G in front of me, driving away fast." \
  -s perception_closed_loop_demo \
  --closed_loop \
  --max_attempts 3 \
  --target_score 0.8 \
  --evaluator_type perception \
  --perception_model yolo11m.pt \
  --perception_tracker botsort.yaml \
  --perception_device 0
```

If GPU memory is limited, use a smaller model or smaller image size:

```bash
python main.py \
  -y config/3dgs-waymo-1137.yaml \
  -p "Add a clear car in the front lane, driving smoothly away." \
  --closed_loop \
  --evaluator_type perception \
  --perception_model yolo11n.pt \
  --perception_imgsz 960 \
  --perception_device 0
```

Default COCO classes are:

```text
0 person, 1 bicycle, 2 car, 3 motorcycle, 5 bus, 7 truck, 9 traffic light, 11 stop sign
```

You can evaluate only vehicles:

```bash
--perception_classes 2,3,5,7
```

Or evaluate every COCO class detected by the model:

```bash
--perception_classes all
```

The perception score is a weighted sum:

```text
0.30 detection coverage
0.25 mean detection confidence
0.20 dominant track coverage
0.15 ID consistency
0.10 bounding-box stability
```

Each closed-loop attempt writes a detailed file under `--evaluation_output_dir`:

```text
attempt_01_perception_evaluation.json
```

The JSON includes the final score, pass/fail flag, metric values, failure reasons, and prompt-refinement suggestions. The prompt refiner uses those suggestions without changing the user's original intent.

## Multimodal Conditioning

LoopDrive can ground auxiliary references into the text prompt before generation starts. The current implementation converts multimodal inputs into textual constraints, because the ChatSim backend is still prompt-driven.

Supported inputs:

- audio instructions via `--audio_prompt_paths`
- reference images via `--reference_image_paths`
- reference videos via `--reference_video_paths`
- sketch images via `--reference_sketch_paths`

Example:

```bash
python main.py \
  -y config/3dgs-waymo-1137.yaml \
  -p "Add a vehicle in front of me." \
  --reference_image_paths /path/to/reference_car.jpg \
  --reference_sketch_paths /path/to/layout_sketch.png \
  --audio_prompt_paths /path/to/voice_instruction.wav
```

The system writes a multimodal conditioning report under `--conditioning_report_dir`, including the raw prompt, fused prompt, and parsed auxiliary cues.

## Long-Tail Scenario Control

LoopDrive also supports explicit long-tail scenario tags:

- `animal_crossing`
- `traffic_accident`
- `heavy_rain`
- `fog`
- `snow`

These tags are injected through prompt augmentation and, when needed, video post-processing.

Example:

```bash
python main.py \
  -y config/3dgs-waymo-1137.yaml \
  -p "Add a stopped vehicle on the right shoulder." \
  --long_tail_scenarios traffic_accident,heavy_rain,fog
```

Current implementation details:

- `traffic_accident` adds prompt-level constraints for stopped vehicles and warning obstacles.
- `heavy_rain`, `fog`, and `snow` apply weather-aware video post-processing after rendering.
- `animal_crossing` adds an animated crossing overlay during video post-processing.

## Python Evaluator

The Python callable must accept keyword arguments:

```python
def evaluate(video_path: str, prompt: str, metadata: dict) -> dict:
    return {
        "score": 0.91,
        "passed": True,
        "summary": "passed",
        "metrics": {}
    }
```

Run:

```bash
python main.py \
  -y config/3dgs-waymo-1137.yaml \
  -p "Add a Benz G in front of me, driving away fast." \
  --closed_loop \
  --evaluator_type python \
  --evaluator_python my_eval.module:evaluate
```

## Language Handling

The original project passes user prompts directly into English LLM instructions. The closed-loop refiner adds an explicit language constraint: refined prompts must remain in the same language or mixed-language style as the original user prompt.
