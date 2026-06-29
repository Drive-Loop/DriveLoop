from .drivedreamer2_img_cond_mini_local import *

train_data = '/data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_train/v0.0.2'
test_data = train_data

dataloaders['train']['data_or_config'] = train_data
dataloaders['test']['data_or_config'] = test_data
dataloaders['test']['shuffle'] = False
