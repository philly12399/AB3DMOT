import os
import sys
import click
from xinshuo_io import mkdir_if_missing
import pdb

@click.command()
### Add your options here
@click.option(
    "--root",
    "-r",
    type=str,
    default="/home/philly12399/philly_ssd/ab3dmot/track_exp/BASELINE/car/age5_car",
    help="",
)
@click.option(
    "--eval_config",
    "-ec",
    type=str,
    default="KITTI_eval_gtdet_car.yml",
    help="Name of config file .",
)
def eval(root,eval_config):
    
    for d in sorted(os.listdir(root)):
        path1=os.path.join(root,d)
        if os.path.isdir(os.path.join(path1,'label')):
            print(f"Evaluate {path1}")
            os.system(f"python3 ./scripts/KITTI/evaluate.py --config ./eval_configs/{eval_config} -e {path1}")
        else:
            continue
    
if __name__ == "__main__":
    eval()
