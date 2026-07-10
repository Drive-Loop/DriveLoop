"""Parallel hdmap stage for the nuScenes cam_all conversion.

The serial converter renders hdmaps at ~4.5 it/s single-process (~73 h for
trainval). This tool splits the stage into three phases:

  A. Extract per-record hdmap inputs (poses, calib, intrinsics, location) with
     the devkit loaded once in the main process; write per-worker pickle shards.
  B. Workers render hdmaps with NuScenesMap objects only (no devkit copy) and
     write PNG-encoded shards into per-worker LMDBs.
  C. Merge worker shards into the final hdmaps LMDB, byte-identical format to
     the serial LmdbWriter.write_image path.

--verify N byte-compares the parallel render against the serial
NuScenesConverter._get_hdmap on N random records before any writes.

Run AFTER the labels stage is complete; do not run concurrently with the
serial converter (both write the same hdmap directories).
"""
import argparse
import gc
import os
import pickle
import random
import shutil
import sys
from io import BytesIO
from multiprocessing import get_context

import numpy as np
from PIL import Image, PngImagePlugin
from pyquaternion import Quaternion
from tqdm import tqdm

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
if CUR_DIR not in sys.path:
    sys.path.insert(0, CUR_DIR)
DREAMER_DATASETS_ROOT = os.path.abspath(os.path.join(CUR_DIR, '..', '..'))
if DREAMER_DATASETS_ROOT not in sys.path:
    sys.path.insert(0, DREAMER_DATASETS_ROOT)

import lmdb  # noqa: E402
from nuscenes.map_expansion.map_api import NuScenesMap, NuScenesMapExplorer  # noqa: E402

from dreamer_datasets import load_dataset  # noqa: E402
from dreamer_datasets.datasets.lmdb_dataset import LmdbWriter  # noqa: E402
from nuscenes_converter import (  # noqa: E402
    get_map_geom,
    line_geoms_to_vectors,
    poly_geoms_to_vectors,
    preprocess_map,
    quaternion_yaw,
    view_points_depth,
)

CLASS2LABEL = {
    'road_divider': 0,
    'lane_divider': 0,
    'ped_crossing': 1,
    'contours': 2,
    'others': -1,
}
MAP_NAMES = [
    'boston-seaport',
    'singapore-onenorth',
    'singapore-hollandvillage',
    'singapore-queenstown',
]
PATCH_SIZE = 102.4


def build_maps(data_dir, locations=None):
    maps = {}
    explorers = {}
    for name in locations if locations is not None else MAP_NAMES:
        maps[name] = NuScenesMap(dataroot=data_dir, map_name=name)
        explorers[name] = NuScenesMapExplorer(maps[name])
    return maps, explorers


def render_hdmap(record, nusc_maps, map_explorer):
    """Line-for-line replica of NuScenesConverter._get_hdmap from precomputed inputs."""
    cam_intrinsic = np.array(record['cam_intrinsic'])
    imsize = (record['width'], record['height'])
    ego2global_translation = np.array(record['ego_translation'])
    rotation = Quaternion(record['ego_rotation'])
    map_pose = ego2global_translation[:2]
    patch_box = (map_pose[0], map_pose[1], PATCH_SIZE, PATCH_SIZE)
    patch_angle = quaternion_yaw(rotation) / np.pi * 180
    location = record['location']
    nusc_map = nusc_maps[location]
    explorer = map_explorer[location]
    line_geom = get_map_geom(patch_box, patch_angle, ['road_divider', 'lane_divider'], nusc_map, explorer)
    line_vector_dict = line_geoms_to_vectors(line_geom)
    ped_geom = get_map_geom(patch_box, patch_angle, ['ped_crossing'], nusc_map, explorer)
    ped_vector_list = line_geoms_to_vectors(ped_geom)['ped_crossing']
    polygon_geom = get_map_geom(patch_box, patch_angle, ['road_segment', 'lane'], nusc_map, explorer)
    poly_bound_list = poly_geoms_to_vectors(polygon_geom)
    vectors = []
    for line_type, vects in line_vector_dict.items():
        for line, length in vects:
            vectors.append((line.astype(float), length, CLASS2LABEL.get(line_type, -1)))
    for ped_line, length in ped_vector_list:
        vectors.append((ped_line.astype(float), length, CLASS2LABEL.get('ped_crossing', -1)))
    for contour, length in poly_bound_list:
        vectors.append((contour.astype(float), length, CLASS2LABEL.get('contours', -1)))
    filtered_vectors = []
    for pts, pts_num, vec_type in vectors:
        if vec_type != -1:
            filtered_vectors.append({'pts': pts, 'pts_num': pts_num, 'type': vec_type})
    for vector in filtered_vectors:
        pts = vector['pts']
        vector['pts'] = np.concatenate((pts, np.zeros((pts.shape[0], 1))), axis=1)
    cs_translation = np.array(record['cs_translation'])
    cs_rotation = Quaternion(record['cs_rotation'])
    for vector in filtered_vectors:
        assert vector['pts'][:, 2].sum() == 0
        this_pts = vector['pts'].T
        this_pts = this_pts - cs_translation.reshape((-1, 1))
        this_pts = np.dot(cs_rotation.rotation_matrix.T, this_pts)
        this_pts, this_depth = view_points_depth(this_pts, cam_intrinsic, normalize=True)
        this_pts = this_pts[:, this_depth > 1e-3]
        vector['pts_num'] -= (this_depth <= 1e-3).sum()
        this_pts = this_pts[:2, :]
        vector['pts'] = this_pts.T
    map_canvas_size = [imsize[1], imsize[0]]
    semantic_masks = preprocess_map(filtered_vectors, map_canvas_size, max_channel=3, thickness=10)
    color_base_map = 255 * np.ones((imsize[1], imsize[0], 3), dtype=np.uint8)
    color_base_map[..., 0] *= ~semantic_masks[0]
    color_base_map[..., 1] *= ~semantic_masks[1]
    color_base_map[..., 2] *= ~semantic_masks[2]
    color_base_map = 255 - color_base_map
    color_base_map = color_base_map[:, :, ::-1]
    return Image.fromarray(color_base_map)


def png_bytes(image):
    """Replicates the PIL branch of LmdbWriter.write_image byte-for-byte."""
    metadata = PngImagePlugin.PngInfo()
    for key, value in image.info.items():
        if isinstance(key, str) and isinstance(value, str):
            metadata.add_text(key, value)
    with BytesIO() as output_bytes:
        image.save(output_bytes, format='png', pnginfo=metadata)
        return output_bytes.getvalue()


def extract_inputs(nusc, label_dataset):
    scene_locations = {}
    records = []
    for i in tqdm(range(len(label_dataset)), desc='Extract hdmap inputs'):
        label_dict = label_dataset[i]
        cam_token = label_dict['cam_token']
        scene_token = label_dict['scene_token']
        if scene_token not in scene_locations:
            log_token = nusc.get('scene', scene_token)['log_token']
            scene_locations[scene_token] = nusc.get('log', log_token)['location']
        cam_record = nusc.get('sample_data', cam_token)
        pose_record = nusc.get('ego_pose', cam_record['ego_pose_token'])
        cs_record = nusc.get('calibrated_sensor', cam_record['calibrated_sensor_token'])
        records.append(
            {
                'data_index': label_dict['data_index'],
                'cam_token': cam_token,
                'scene_token': scene_token,
                'location': scene_locations[scene_token],
                'ego_translation': list(pose_record['translation']),
                'ego_rotation': list(pose_record['rotation']),
                'cs_translation': list(cs_record['translation']),
                'cs_rotation': list(cs_record['rotation']),
                'cam_intrinsic': cs_record['camera_intrinsic'],
                'width': cam_record['width'],
                'height': cam_record['height'],
            }
        )
    return records


def worker_main(job):
    shard_pickle, shard_db, data_dir = job
    with open(shard_pickle, 'rb') as f:
        records = pickle.load(f)
    locations = sorted({r['location'] for r in records})
    nusc_maps, map_explorer = build_maps(data_dir, locations)
    writer = LmdbWriter(shard_db)
    for record in records:
        image = render_hdmap(record, nusc_maps, map_explorer)
        writer.write_image(record['data_index'], image)
    writer.write_config(data_name='image_hdmap')
    writer.close()
    return shard_db, len(records)


def merge_shards(shard_dbs, final_path, expected_total):
    writer = LmdbWriter(final_path)
    merged = 0
    for shard_db in shard_dbs:
        env = lmdb.open(shard_db, readonly=True, lock=False)
        with env.begin() as txn:
            with txn.cursor() as cursor:
                for key, value in cursor:
                    writer.write_image_bytes(key.decode(), value)
                    merged += 1
        env.close()
    assert merged == expected_total, 'merged {} != expected {}'.format(merged, expected_total)
    writer.write_config(data_name='image_hdmap')
    writer.close()
    return merged


def run_verification(converter, records, nusc_maps, map_explorer, num_verify, seed=0):
    rng = random.Random(seed)
    picks = rng.sample(range(len(records)), min(num_verify, len(records)))
    for count, idx in enumerate(picks, 1):
        record = records[idx]
        serial_image = converter._get_hdmap(record['cam_token'], record['scene_token'])
        parallel_image = render_hdmap(record, nusc_maps, map_explorer)
        if png_bytes(serial_image) != png_bytes(parallel_image):
            raise AssertionError(
                'verification mismatch at data_index {} (cam_token {})'.format(
                    record['data_index'], record['cam_token']
                )
            )
        if count % 8 == 0:
            print('verified {}/{}'.format(count, len(picks)))
    print('verification passed on {} records'.format(len(picks)))


def main():
    parser = argparse.ArgumentParser(description='parallel hdmap conversion')
    parser.add_argument('--nusc_version', type=str, default='v1.0-trainval')
    parser.add_argument('--data_root', type=str, required=True)
    parser.add_argument('--save_root', type=str, required=True)
    parser.add_argument('--save_version', type=str, default='v0.0.1')
    parser.add_argument('--splits', type=str, nargs='+', default=['train', 'val'])
    parser.add_argument('--workers', type=int, default=0)
    parser.add_argument('--verify', type=int, default=64)
    parser.add_argument('--shard_dir', type=str, default='')
    args = parser.parse_args()

    workers = args.workers
    if workers <= 0:
        workers = int(os.environ.get('DRIVELOOP_HDMAP_WORKERS', '0'))
    if workers <= 0:
        workers = min(6, max(1, (os.cpu_count() or 4) - 2))

    data_dir = os.path.join(args.data_root, args.nusc_version)
    save_path = os.path.join(args.save_root, args.nusc_version)
    shard_dir = args.shard_dir or os.path.join(save_path, 'hdmap_shards_tmp')

    label_paths = {}
    hdmap_paths = {}
    for split in args.splits:
        label_paths[split] = os.path.join(save_path, 'cam_all_' + split, args.save_version, 'labels')
        hdmap_paths[split] = os.path.join(save_path, 'cam_all_' + split, args.save_version, 'hdmaps')
        config_path = os.path.join(label_paths[split], 'config.json')
        assert os.path.exists(config_path), 'labels incomplete for split {}: {}'.format(split, config_path)

    print('workers: {}'.format(workers))
    print('loading devkit for input extraction...')
    from nuscenes_converter import NuScenesConverter

    converter = NuScenesConverter(
        data_dir=data_dir,
        version=args.nusc_version,
        save_path=save_path,
        save_version=args.save_version,
    )
    split_records = {}
    for split in args.splits:
        label_dataset = load_dataset(label_paths[split])
        split_records[split] = extract_inputs(converter.nusc, label_dataset)
        print('{}: {} records'.format(split, len(split_records[split])))

    if args.verify > 0:
        verify_split = args.splits[0]
        run_verification(
            converter,
            split_records[verify_split],
            converter.nusc_maps,
            converter.map_explorer,
            args.verify,
        )

    del converter
    gc.collect()

    ctx = get_context('spawn')
    for split in args.splits:
        records = split_records[split]
        os.makedirs(shard_dir, exist_ok=True)
        jobs = []
        chunk = int(np.ceil(len(records) / workers))
        for w in range(workers):
            part = records[w * chunk : (w + 1) * chunk]
            if not part:
                continue
            shard_pickle = os.path.join(shard_dir, '{}_inputs_{:02d}.pkl'.format(split, w))
            shard_db = os.path.join(shard_dir, '{}_shard_{:02d}'.format(split, w))
            with open(shard_pickle, 'wb') as f:
                pickle.dump(part, f)
            jobs.append((shard_pickle, shard_db, data_dir))
        print('{}: {} worker jobs'.format(split, len(jobs)))
        with ctx.Pool(processes=len(jobs)) as pool:
            results = []
            for shard_db, count in pool.imap_unordered(worker_main, jobs):
                results.append((shard_db, count))
                print('shard done: {} ({} records)'.format(shard_db, count))
        shard_dbs = sorted(db for db, _ in results)
        total = sum(count for _, count in results)
        assert total == len(records), 'worker total {} != records {}'.format(total, len(records))
        merged = merge_shards(shard_dbs, hdmap_paths[split], len(records))
        print('{}: merged {} hdmaps into {}'.format(split, merged, hdmap_paths[split]))
        shutil.rmtree(shard_dir)

    print('parallel hdmap conversion complete')


if __name__ == '__main__':
    main()
