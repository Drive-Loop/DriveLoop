from .drivedreamer2_img_cond_mini_local import *

# DD2 fine-tune on full nuScenes trainval (A10 24GB, single GPU).
# Trainable subset defaults are env-gated in DriveDreamer2_Trainer:
# temporal/time_mixer unet params + both downsamplers; fuser frozen.
train_data = '/mnt/driveloop_full/processed/nuscenes/v1.0-trainval/cam_all_train/v0.0.2'
test_data = '/mnt/driveloop_full/processed/nuscenes/v1.0-trainval/cam_all_val/v0.0.2'
project_dir = '/data/projects/DriveLoop/exp/drivedreamer2_img_cond_trainval_ft_local'
save_path = '/data/projects/DriveLoop/outputs/drivedreamer2_img_cond_trainval_ft'

config['project_dir'] = project_dir
config['dataloaders']['train']['data_or_config'] = train_data
config['dataloaders']['train']['num_workers'] = 1
config['dataloaders']['test']['data_or_config'] = test_data
config['dataloaders']['test']['shuffle'] = False
config['test']['save_dir'] = save_path
config['models']['enable_gradient_checkpointing'] = True
config['optimizers']['lr'] = 5e-5
config['train']['max_epochs'] = 1
config['train']['checkpoint_interval'] = 0.1
config['train']['checkpoint_total_limit'] = 3
config['train']['log_interval'] = 50
config['train']['max_grad_norm'] = 1.0
config['train']['resume'] = False
config['dataloaders']['train']['resample_num_workers'] = 0
config['dataloaders']['train']['resample_batch_size'] = 64
