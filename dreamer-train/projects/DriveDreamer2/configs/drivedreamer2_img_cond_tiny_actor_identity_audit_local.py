from .drivedreamer2_img_cond_mini_local import *

test_data = 'outputs/driveloop/tiny_actor_identity_runtime_dataset/cam_front_8/v0.0.1'
save_path = 'outputs/driveloop/tiny_actor_identity_runtime_audit/dd2_baseline_output'

config['dataloaders']['test']['data_or_config'] = test_data
config['dataloaders']['test']['frame_num'] = 8
config['dataloaders']['test']['cam_num'] = 1
config['dataloaders']['test']['is_multiview'] = False
config['dataloaders']['test']['view'] = 'CAM_FRONT'
config['dataloaders']['test']['shuffle'] = False
config['dataloaders']['test']['num_workers'] = 0
config['test']['save_dir'] = save_path
config['test']['frame_num'] = 8
