from .drivedreamer2_img_cond_mini_local import *

train_data = '/data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_train/v0.0.2'
test_data = train_data
project_dir = '/data/projects/DriveLoop/exp/drivedreamer2_img_cond_mini_train_local'
save_path = '/data/projects/DriveLoop/outputs/drivedreamer2_img_cond_mini_train'

config['project_dir'] = project_dir
config['dataloaders']['train']['data_or_config'] = train_data
config['dataloaders']['test']['data_or_config'] = test_data
config['dataloaders']['test']['shuffle'] = False
config['test']['save_dir'] = save_path
