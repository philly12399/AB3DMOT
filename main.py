# Author: Xinshuo Weng
# email: xinshuo.weng@gmail.com

from __future__ import print_function
import matplotlib; matplotlib.use('Agg')
import os, numpy as np, time, sys, argparse
from AB3DMOT_libs.utils import Config, get_subfolder_seq, initialize
from AB3DMOT_libs.io import load_detection, get_saving_dir, get_frame_det, save_results, save_affinity
from scripts.post_processing.combine_trk_cat import combine_trk_cat
from xinshuo_io import mkdir_if_missing, save_txt_file
from xinshuo_miscellaneous import get_timestring, print_log

def parse_args():
    parser = argparse.ArgumentParser(description='AB3DMOT')
    parser.add_argument('-c','--config', type=str, required=True, help='Config file path')
    parser.add_argument('--dataset', type=str, default='nuScenes', help='KITTI, nuScenes, Wayside')
    parser.add_argument('--split', type=str, default='', help='train, val, test')
    parser.add_argument('--det_name', type=str, default='', help='pointrcnn')
    args = parser.parse_args()
    return args

def main_per_cat(cfg, cat, log, ID_start, seq_cfg=None):

    # get data-cat-split specific path
    result_sha = '%s_%s_%s' % (cfg.det_name, cat, cfg.split)
    all_sha = '%s_%s_%s' % (cfg.det_name, 'all', cfg.split)
    # det_root = os.path.join('./data', cfg.dataset, 'detection', result_sha)
    det_root = os.path.join('./data', cfg.dataset, 'detection', cfg.det_name)
    if(os.path.exists(det_root) == False):
        print(f"Didn't find det path {det_root}")
        det_root = os.path.join('./data', cfg.dataset, 'detection', all_sha)
        print(f"Find det path {det_root} instead.")        
        if(os.path.exists(det_root) == False):
            print(f"Didn't find det path {det_root}")            
            det_root = os.path.join('./data', cfg.dataset, 'detection', result_sha)
            print(f"Find det path {det_root} instead.")        
            if(os.path.exists(det_root) == False): 
                print(f"Didn't find det path {det_root}")           
                assert False
    subfolder, det_id2str, hw, _, data_root = get_subfolder_seq(cfg.dataset, cfg.split)
    if(seq_cfg is not None): seq_eval = seq_cfg
    
  
    trk_root = os.path.join(data_root, 'tracking')
    save_dir = os.path.join(cfg.save_root, result_sha + '_H%d' % cfg.num_hypo); mkdir_if_missing(save_dir)
    # create eval dir for each hypothesis 
    eval_dir_dict = dict()
    for index in range(cfg.num_hypo):
        eval_dir_dict[index] = os.path.join(save_dir, 'data_%d' % index); mkdir_if_missing(eval_dir_dict[index]) 		

    # loop every sequence
    seq_count = 0
    total_time, total_frames = 0.0, 0
    for seq_name in seq_eval:
        seq_file = os.path.join(det_root, seq_name+'.txt')
        seq_dets, flag = load_detection(seq_file, format=cfg.dataset, cat=cat) 				# load detection			
        if not flag: continue									# no detection

        # create folders for saving
        eval_file_dict, save_trk_dir, affinity_dir, affinity_vis = \
            get_saving_dir(eval_dir_dict, seq_name, save_dir, cfg.num_hypo)	

        # initialize tracker
        tracker, frame_list = initialize(cfg, trk_root, save_dir, subfolder, seq_name, cat, ID_start, hw, log)

        # loop over frame
        min_frame, max_frame = int(frame_list[0]), int(frame_list[-1])
        for frame in range(min_frame, max_frame + 1):
            # add an additional frame here to deal with the case that the last frame, although no detection
            # but should output an N x 0 affinity for consistency
            
            # logging
            print_str = 'processing %s %s: %d/%d, %d/%d   \r' % (result_sha, seq_name, seq_count, \
                len(seq_eval), frame, max_frame)
            sys.stdout.write(print_str)
            sys.stdout.flush()

            # tracking by detection
            dets_frame = get_frame_det(seq_dets, frame, format=cfg.dataset)
            since = time.time()
            results, affi = tracker.track(dets_frame, frame, seq_name)		
            total_time += time.time() - since

            # saving affinity matrix, between the past frame and current frame
            # e.g., for 000006.npy, it means affinity between frame 5 and 6
            # note that the saved value in affinity can be different in reality because it is between the 
            # original detections and ego-motion compensated predicted tracklets, rather than between the 
            # actual two sets of output tracklets
            save_affi_file = os.path.join(affinity_dir, '%06d.npy' % frame)
            save_affi_vis  = os.path.join(affinity_vis, '%06d.txt' % frame)
            if (affi is not None) and (affi.shape[0] + affi.shape[1] > 0): 
                # save affinity as long as there are tracklets in at least one frame
                np.save(save_affi_file, affi)

                # cannot save for visualization unless both two frames have tracklets
                if affi.shape[0] > 0 and affi.shape[1] > 0:
                    save_affinity(affi, save_affi_vis)

            # saving trajectories, loop over each hypothesis
            for hypo in range(cfg.num_hypo):
                save_trk_file = os.path.join(save_trk_dir[hypo], '%06d.txt' % frame)
                save_trk_file = open(save_trk_file, 'w')
                for result_tmp in results[hypo]:				# N x 15
                    save_results(result_tmp, save_trk_file, eval_file_dict[hypo], \
                        det_id2str, frame, cfg.score_threshold, format=cfg.dataset)
                save_trk_file.close()

            total_frames += 1
        seq_count += 1

        for index in range(cfg.num_hypo): 
            eval_file_dict[index].close()
            ID_start = max(ID_start, tracker.ID_count[index])

    print_log('%s, %25s: %4.f seconds for %5d frames or %6.1f FPS, metric is %s = %.2f' % \
        (cfg.dataset, result_sha, total_time, total_frames, total_frames / total_time, \
        tracker.metric, tracker.thres), log=log)
    
    return ID_start

def main(args):

    # load config files
    # config_path = './configs/%s.yml' % args.dataset
    config_path = args.config
    cfg, settings_show = Config(config_path)

    # overwrite split and detection method
    if args.split is not '': cfg.split = args.split
    if args.det_name is not '': cfg.det_name = args.det_name
    
    # print configs
    time_str = get_timestring()
    log = os.path.join(cfg.save_root, 'log/log_%s_%s_%s.txt' % (time_str, cfg.dataset, cfg.split))
    mkdir_if_missing(log); log = open(log, 'w')
    for idx, data in enumerate(settings_show):
        print_log(data, log, display=False)

    # global ID counter used for all categories, not start from 1 for each category to prevent different 
    # categories of objects have the same ID. This allows visualization of all object categories together
    # without ID conflicting, Also use 1 (not 0) as start because MOT benchmark requires positive ID
    ID_start = 1	
    cat = cfg.cat_list[0]						
    if(cat.lower() == 'car'):
        seq_eval = ['0001', '0002', '0005', '0007', '0008', '0009', '0011', '0018', '0019', '0020']    # val
    elif(cat.lower() == 'cyclist'):
        seq_eval = ['0000', '0005', '0013', '0015', '0016', '0019']    # val
    # run tracking for each category
    for cat in cfg.cat_list:
        ID_start = main_per_cat(cfg, cat, log, ID_start,seq_eval)

    # combine results for every category
    print_log('\ncombining results......', log=log)
    combine_trk_cat(cfg.split, cfg.dataset, cfg.det_name, 'H%d' % cfg.num_hypo, cfg.num_hypo,config_path,seq_eval)
    print_log('\nDone!', log=log)
    log.close()

if __name__ == '__main__':

    args = parse_args()
    main(args)