from .drivedreamer2_img_cond_mini_local import *

# Short overfit smoke on nuScenes mini: verifies the training loop end to end
# (loss decreases, checkpoint + gligen export written) before any trainval run.
train_data = '/data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_train/v0.0.2'
project_dir = '/data/projects/DriveLoop/exp/drivedreamer2_img_cond_mini_ft_smoke_local'

config['project_dir'] = project_dir
config['dataloaders']['train']['data_or_config'] = train_data
config['dataloaders']['train']['num_workers'] = 2
config['models']['enable_gradient_checkpointing'] = True
config['optimizers']['lr'] = 5e-5
config['schedulers']['num_warmup_steps'] = 10
config['train']['max_epochs'] = 1
config['train']['checkpoint_interval'] = 0.5
config['train']['checkpoint_total_limit'] = 2
config['train']['log_interval'] = 10
config['train']['max_grad_norm'] = 1.0
config['train']['resume'] = False
