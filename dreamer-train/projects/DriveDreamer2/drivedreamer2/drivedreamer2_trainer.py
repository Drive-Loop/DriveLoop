import copy
import json
import os

import torch
import torch.nn as nn
import torch.nn.functional as F
from diffusers.optimization import get_scheduler as build_lr_scheduler

from dreamer_datasets import load_dataset
from dreamer_models import DriveDreamer2Pipeline
from dreamer_train import Trainer
from . import drivedreamer2_transforms
from .drivedreamer2_utils import GLIGEN_WEIGHT_NAME, VideoCollator, VideoSampler

DEFAULT_TRAIN_PATTERNS = 'temporal,time_mixer'
ADDED_TIME_IDS = (6.0, 127.0, 0.02)  # fps-1, motion_bucket_id, noise_aug_strength (pipeline defaults)


def resolve_train_patterns():
    raw = os.environ.get('DRIVELOOP_FT_TRAIN_PATTERNS', DEFAULT_TRAIN_PATTERNS)
    patterns = [p.strip() for p in raw.split(',') if p.strip()]
    if not patterns:
        raise ValueError('DRIVELOOP_FT_TRAIN_PATTERNS resolved to an empty pattern list')
    return patterns


def select_trainable_param_names(named_params, patterns):
    """Return the subset of parameter names matched by any substring pattern."""
    selected = []
    for name, _ in named_params:
        if any(pattern in name for pattern in patterns):
            selected.append(name)
    return selected


def panoramic_from_records(tensor, cam_num, frame_num):
    """(cam_num*frame_num, C, H, W) cam-major records -> (frame_num, C, H, W*cam_num).

    Mirrors the reshape in DriveDreamer2_Tester.test exactly.
    """
    if tensor.shape[0] != cam_num * frame_num:
        raise ValueError(
            'expected leading dim {} (cam_num {} * frame_num {}), got {}'.format(
                cam_num * frame_num, cam_num, frame_num, tensor.shape[0]
            )
        )
    return (
        tensor.reshape(cam_num, frame_num, *tensor.shape[1:])
        .permute(1, 2, 3, 0, 4)
        .flatten(3, 4)
    )


def edm_scalings(sigma):
    """EDM preconditioning constants matching diffusers EulerDiscreteScheduler with
    prediction_type='v_prediction' and timestep_type='continuous' (sigma_data = 1.0).

    scale_model_input divides by sqrt(sigma^2 + 1) (c_in); step() reconstructs
    denoised = model_output * (-sigma / sqrt(sigma^2 + 1)) + sample / (sigma^2 + 1).
    """
    c_in = 1.0 / torch.sqrt(sigma**2 + 1.0)
    c_skip = 1.0 / (sigma**2 + 1.0)
    c_out = -sigma / torch.sqrt(sigma**2 + 1.0)
    c_noise = 0.25 * torch.log(sigma)
    return c_in, c_skip, c_out, c_noise


def edm_loss_weight(sigma):
    """lambda(sigma) * c_out(sigma)^2 for sigma_data = 1.0: (sigma^2 + 1) / sigma^2."""
    return (sigma**2 + 1.0) / sigma**2


def build_gligen_state_dict(unet_state_dict, gd_state_dict, bd_state_dict, meta):
    """Assemble a state dict in the exact format DriveDreamer2_LoaderMixin.load_weights expects."""
    out = {}
    for name, param in unet_state_dict.items():
        out['unet.' + name] = param
    for name, param in gd_state_dict.items():
        out['grounding_downsampler.' + name] = param
    for name, param in bd_state_dict.items():
        out['box_downsampler.' + name] = param
    out['meta'] = copy.deepcopy(meta)
    return out


class DriveDreamer2TrainModule(nn.Module):
    """Wraps unet + downsamplers (+ frozen vae) and computes the SVD/EDM training loss
    whose parameterization is bit-consistent with DriveDreamer2Pipeline.__call__.
    """

    def __init__(self, unet, grounding_downsampler, box_downsampler, vae, frame_num, cam_num):
        super().__init__()
        self.unet = unet
        self.grounding_downsampler = grounding_downsampler
        self.box_downsampler = box_downsampler
        self.vae = vae
        self.frame_num = frame_num
        self.cam_num = cam_num
        self.sigma_pmean = float(os.environ.get('DRIVELOOP_FT_SIGMA_PMEAN', '1.0'))
        self.sigma_pstd = float(os.environ.get('DRIVELOOP_FT_SIGMA_PSTD', '1.6'))
        self.cond_drop_prob = float(os.environ.get('DRIVELOOP_FT_COND_DROP_PROB', '0.1'))

    def enable_fuser(self, enabled=True):
        for module in self.unet.modules():
            if type(module).__name__ == 'GatedSelfAttentionDense':
                module.enabled = enabled

    @torch.no_grad()
    def _encode_frames(self, frames, chunk=2):
        latents = []
        for i in range(0, frames.shape[0], chunk):
            posterior = self.vae.encode(frames[i : i + chunk].half()).latent_dist
            latents.append(posterior.sample() * self.vae.config.scaling_factor)
        return torch.cat(latents, dim=0)

    def forward(self, batch_dict):
        device = next(self.unet.parameters()).device

        images = batch_dict['image'].to(device)
        gd_input = batch_dict['grounding_downsampler_input'].to(device)
        bd_input = batch_dict['box_downsampler_input'].to(device)
        prompt_embeds = batch_dict['prompt_embeds'].to(device)

        frames = panoramic_from_records(images, self.cam_num, self.frame_num)
        gd_input = panoramic_from_records(gd_input, self.cam_num, self.frame_num)
        bd_input = panoramic_from_records(bd_input, self.cam_num, self.frame_num)

        prompt = prompt_embeds[0:1]
        if prompt.dim() == 2:
            prompt = prompt[:, None]
        prompt = prompt.to(self.unet.dtype)

        # Ground-truth latents and the frame-0 image condition, both as in inference.
        x0 = self._encode_frames(frames)[None]  # (1, F, 4, h, w)
        condition_latents = torch.zeros_like(x0)
        with torch.no_grad():
            cond0 = self.vae.encode(frames[0:1].half()).latent_dist.sample()
            condition_latents[0, 0] = cond0[0] * self.vae.config.scaling_factor

        gd_feat = self.grounding_downsampler(gd_input.to(self.unet.dtype))
        gd_feat = gd_feat.reshape(1, self.frame_num, *gd_feat.shape[1:])
        bd_feat = self.box_downsampler(bd_input.to(self.unet.dtype))
        bd_feat = bd_feat.reshape(1, self.frame_num, *bd_feat.shape[1:])

        # Condition dropout mirrors the CFG negative branch (zeroed prompt and
        # zeroed downsampler outputs; the image condition is kept on both branches).
        if self.training and self.cond_drop_prob > 0 and torch.rand(()) < self.cond_drop_prob:
            prompt = torch.zeros_like(prompt)
            gd_feat = torch.zeros_like(gd_feat)
            bd_feat = torch.zeros_like(bd_feat)

        sigma = torch.exp(
            self.sigma_pmean + self.sigma_pstd * torch.randn(1, device=device, dtype=torch.float32)
        )
        c_in, c_skip, c_out, c_noise = edm_scalings(sigma)

        noise = torch.randn_like(x0.float())
        x_t = x0.float() + sigma * noise
        model_input = (x_t * c_in).to(self.unet.dtype)
        model_input = torch.cat(
            [model_input, condition_latents.to(self.unet.dtype), gd_feat, bd_feat], dim=2
        )

        added_time_ids = torch.tensor([ADDED_TIME_IDS], device=device, dtype=self.unet.dtype)
        model_output = self.unet(
            model_input,
            c_noise.reshape(()),
            encoder_hidden_states=prompt,
            added_time_ids=added_time_ids,
            num_cams=1,
            return_dict=False,
        )[0]

        denoised = model_output.float() * c_out + x_t * c_skip
        weight = edm_loss_weight(sigma)
        loss = (weight * F.mse_loss(denoised, x0.float(), reduction='none')).mean()
        return {'diff_loss': loss}


class DriveDreamer2_Trainer(Trainer):
    def get_dataloaders(self, data_config):
        self.data_config = data_config
        dataset = load_dataset(data_config.data_or_config)
        transform = getattr(drivedreamer2_transforms, data_config.transform.pop('type'))(
            **data_config.transform
        )
        dataset.set_transform(transform)

        self.cam_num = data_config.cam_num
        self.frame_num = data_config.frame_num
        batch_size_per_gpu = self.frame_num * self.cam_num

        dataloader = torch.utils.data.DataLoader(
            dataset,
            sampler=VideoSampler(
                dataset,
                batch_size=batch_size_per_gpu,
                frame_num=self.frame_num,
                cam_num=self.cam_num,
                video_split_rate=data_config.get('video_split_rate', 1),
                hz_factor=data_config.hz_factor,
                mv_video=data_config.is_multiview,
                view=data_config.view,
                shuffle=data_config.shuffle,
                logger=self.logger,
                resample_num_workers=data_config.get('resample_num_workers', 0),
                resample_batch_size=data_config.get('resample_batch_size', 8),
            ),
            collate_fn=VideoCollator(
                frame_num=self.frame_num,
                img_mask_type=data_config.img_mask_type,
                img_mask_num=data_config.img_mask_num,
            ),
            batch_size=batch_size_per_gpu,
            num_workers=data_config.num_workers,
        )
        return dataloader

    def get_models(self, model_config):
        mode = model_config.get('mode', 'img_cond')
        if mode != 'img_cond':
            raise NotImplementedError('DriveDreamer2_Trainer currently supports img_cond only')

        scheduler_config_path = os.path.join(
            model_config.pretrained, 'scheduler', 'scheduler_config.json'
        )
        with open(scheduler_config_path, 'r', encoding='utf-8') as f:
            scheduler_config = json.load(f)
        prediction_type = scheduler_config.get('prediction_type')
        timestep_type = scheduler_config.get('timestep_type')
        if prediction_type != 'v_prediction' or timestep_type != 'continuous':
            raise NotImplementedError(
                'training loss implements v_prediction + continuous timesteps; scheduler config '
                'reports prediction_type={} timestep_type={}'.format(prediction_type, timestep_type)
            )

        variant = 'fp16' if self.mixed_precision == 'fp16' else None
        pipeline = DriveDreamer2Pipeline.from_pretrained(
            model_config.pretrained,
            torch_dtype=self.dtype,
            variant=variant,
            local_files_only=model_config.get('local_files_only', True),
            safety_checker=None,
        )

        weight_path = model_config.get('weight_path', None)
        if weight_path is None:
            raise ValueError('weight_path pointing at the released gligen weights is required')
        if os.path.isdir(weight_path):
            weight_path = os.path.join(weight_path, GLIGEN_WEIGHT_NAME)
        raw_state = torch.load(weight_path, map_location='cpu')
        self._gligen_meta = copy.deepcopy(raw_state['meta'])
        del raw_state
        self.logger.info('load gligen weights from {}'.format(weight_path))
        pipeline.load_weights(weight_path)

        model = DriveDreamer2TrainModule(
            unet=pipeline.unet,
            grounding_downsampler=pipeline.grounding_downsampler,
            box_downsampler=pipeline.box_downsampler,
            vae=pipeline.vae,
            frame_num=self.kwargs.get('frame_num', self.frame_num),
            cam_num=self.cam_num,
        )
        model.enable_fuser(True)
        model.vae.requires_grad_(False)
        model.vae.eval()

        patterns = resolve_train_patterns()
        for param in model.unet.parameters():
            param.requires_grad_(False)
        selected = select_trainable_param_names(model.unet.named_parameters(), patterns)
        selected_set = set(selected)
        for name, param in model.unet.named_parameters():
            if name in selected_set:
                param.requires_grad_(True)
                param.data = param.data.float()

        train_downsamplers = os.environ.get('DRIVELOOP_FT_TRAIN_DOWNSAMPLERS', '1') == '1'
        for module in (model.grounding_downsampler, model.box_downsampler):
            module.requires_grad_(train_downsamplers)
            if train_downsamplers:
                module.float()

        train_fuser = os.environ.get('DRIVELOOP_FT_TRAIN_FUSER', '0') == '1'
        if train_fuser:
            for mod_name, module in model.unet.named_modules():
                if type(module).__name__ == 'GatedSelfAttentionDense':
                    for param in module.parameters():
                        param.requires_grad_(True)
                        param.data = param.data.float()

        if model_config.get('enable_gradient_checkpointing', False):
            if hasattr(model.unet, 'enable_gradient_checkpointing'):
                model.unet.enable_gradient_checkpointing()
                self.logger.info('gradient checkpointing enabled on unet')

        trainable = [n for n, p in model.named_parameters() if p.requires_grad]
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for n, p in model.named_parameters() if p.requires_grad)
        self.logger.info(
            'trainable params: {} tensors, {}/{} elements ({:.1f}%)'.format(
                len(trainable), trainable_params, total_params, 100.0 * trainable_params / total_params
            )
        )
        audit_path = os.environ.get('DRIVELOOP_FT_AUDIT_PATH')
        if audit_path and self.is_main_process:
            audit = {
                'schema_version': 'dd2_ft_trainable_audit.v0',
                'patterns': patterns,
                'train_downsamplers': train_downsamplers,
                'train_fuser': train_fuser,
                'cond_drop_prob': model.cond_drop_prob,
                'sigma_pmean': model.sigma_pmean,
                'sigma_pstd': model.sigma_pstd,
                'trainable_tensor_count': len(trainable),
                'trainable_element_count': int(trainable_params),
                'total_element_count': int(total_params),
                'trainable_name_sample': trainable[:40],
            }
            with open(audit_path, 'w', encoding='utf-8') as f:
                json.dump(audit, f, indent=2)

        return model

    def get_schedulers(self, scheduler_config):
        return build_lr_scheduler(
            scheduler_config['name'],
            optimizer=self.optimizer,
            num_warmup_steps=scheduler_config.get('num_warmup_steps', 0),
            num_training_steps=self.max_steps,
        )

    def export_gligen_weights(self, output_dir):
        model = self.accelerator.unwrap_model(self.model)
        state = build_gligen_state_dict(
            unet_state_dict={k: v.detach().cpu().half() for k, v in model.unet.state_dict().items()},
            gd_state_dict={
                k: v.detach().cpu().half() for k, v in model.grounding_downsampler.state_dict().items()
            },
            bd_state_dict={
                k: v.detach().cpu().half() for k, v in model.box_downsampler.state_dict().items()
            },
            meta=self._gligen_meta,
        )
        output_path = os.path.join(output_dir, GLIGEN_WEIGHT_NAME)
        torch.save(state, output_path)
        self.logger.info('exported gligen weights to {}'.format(output_path))

    def save_checkpoint_step(self):
        if self._by_epoch:
            checkpoint_interval = int(self.checkpoint_interval * self.epoch_size)
        else:
            checkpoint_interval = int(self.checkpoint_interval)
        will_save = self.cur_step % checkpoint_interval == 0 or self.cur_step == self.max_steps
        super().save_checkpoint_step()
        if will_save and self.is_main_process:
            output_name = 'checkpoint_epoch_{}_step_{}'.format(self.cur_epoch, self.cur_step)
            self.export_gligen_weights(os.path.join(self.model_dir, output_name))
