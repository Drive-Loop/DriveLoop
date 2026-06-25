# DriveLoop Handoff

## Project Goal
Build DriveLoop on top of DriveDreamer-2. DriveDreamer-2 is used as a fixed video-generation backend. DriveLoop adds a closed loop: prompt/condition -> generation -> perception evaluation -> diagnosis -> prompt/condition refinement -> regeneration.

## Important Decision
Do not train DriveDreamer-2 in the first phase. First implement and evaluate DriveLoop as an inference-time closed-loop system. Later, optional downstream training can be added.

## Local Code
Original DriveDreamer-2 code was downloaded locally to:
/Users/tangzimo/Documents/driveloop/DriveDreamer2

Downloaded official DriveDreamer-2 weights locally under:
/Users/tangzimo/Documents/driveloop/DriveDreamer2/DriveDreamer2

## Server
SSH:
ssh -i ~/Downloads/driveloop.pem root@47.245.169.139

Conda:
source /data/miniconda3/bin/activate
conda activate driveloop

Project root:
/data/projects/DriveLoop

Code root:
/data/projects/DriveLoop/DriveDreamer2

## Server Environment Status
GPU works: NVIDIA A10, CUDA driver 12.2.
Conda env works: driveloop.
DriveDreamer-2 imports are working.

PyTorch was upgraded to:
torch 2.4.1+cu121
torch.cuda.is_available() = True
has torch.xpu = True

DriveDreamer-2 dependency issues fixed:
- Installed README dependencies.
- Added missing mmengine.
- Fixed lmdb by reinstalling lmdb==1.4.1.

## Uploaded Assets On Server
DriveDreamer-2 weights:
/data/projects/DriveLoop/pretrained_models/drivedreamer2_img_cond/pytorch_gligen_weights.bin
/data/projects/DriveLoop/pretrained_models/drivedreamer2_video_cond/pytorch_gligen_weights.bin
/data/projects/DriveLoop/pretrained_models/drivedreamer2_wo_img/pytorch_gligen_weights.bin

Prompt embedding:
/data/projects/DriveLoop/clip_text_transform_after_pool_panoramic.pkl

Stable Video Diffusion base model:
/data/projects/DriveLoop/hf_cache/stable-video-diffusion-img2vid-xt-1-1

Note: HuggingFace access required accepting the StabilityAI license for research/non-commercial use.

## Config Created
Created local config:
/data/projects/DriveLoop/DriveDreamer2/dreamer-train/projects/DriveDreamer2/configs/drivedreamer2_img_cond_local.py

Paths were changed to:
/data/projects/DriveLoop/exp
/data/projects/DriveLoop/data/processed/nuscenes/cam_all_train/v0.0.2
/data/projects/DriveLoop/data/processed/nuscenes/cam_all_val/v0.0.2
/data/projects/DriveLoop/clip_text_transform_after_pool_panoramic.pkl
/data/projects/DriveLoop/pretrained_models/drivedreamer2_img_cond/pytorch_gligen_weights.bin
/data/projects/DriveLoop/outputs/drivedreamer2_img_cond
/data/projects/DriveLoop/hf_cache/stable-video-diffusion-img2vid-xt-1-1

## Current Blocker
nuScenes processed data is not present yet:
/data/projects/DriveLoop/data/processed/nuscenes/cam_all_train/v0.0.2
/data/projects/DriveLoop/data/processed/nuscenes/cam_all_val/v0.0.2

Before running the original DriveDreamer-2 baseline, prepare or upload processed nuScenes data.

## Next Recommended Steps
1. Push code-only project to GitHub.
2. Download/clone the GitHub repo locally in the new window.
3. Verify local handoff doc.
4. On server, prepare processed nuScenes data.
5. Run original DriveDreamer-2 img_cond baseline.
6. Add DriveLoop modules:
   - schema.py
   - grounding.py
   - longtail.py
   - condition_builder.py
   - dd2_backend.py
   - evaluator.py
   - refiner.py
   - runner.py
   - logging/history.py
7. Compare open-loop DriveDreamer-2 vs closed-loop DriveLoop.

## Do Not Commit
Do not commit:
- pretrained_models/
- hf_cache/
- data/
- outputs/
- exp/
- pem files
- HuggingFace tokens
- downloaded model weights
