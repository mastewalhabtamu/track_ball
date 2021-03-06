import os
import argparse

from detectron2 import model_zoo
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg

from ball_loader import register_coco_instances


def get_parser():
    parser = argparse.ArgumentParser(
        description="Detectron2 filtered categories trainer from builtin models")
    parser.add_argument("--config-name",
                        default="COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml",
                        help="model .yml file name in configs folder of detectron2",
                        )
    parser.add_argument(
        "--output",
        default="./output",
        help="A directory to save training outputs. ",
    )
    parser.add_argument("--resume", action="store_true",
                        help="Whether trainer resume_or_load should be true")
    parser.add_argument(
        "--opts",
        help="Modify config options using the command-line 'KEY VALUE' pairs",
        default=[],
        nargs=argparse.REMAINDER,
    )
    return parser

if __name__ == "__main__":
    args = get_parser().parse_args()

    # resister datasets filtered by category
    dataset_name = 'ball_train'
    metadata = {}
    json_file = f'../data/annotations/annotations/instances_train2017.json'
    img_root = f'../data/train2017/'
    category_names = ['sports ball']
    register_coco_instances(dataset_name, {}, json_file,
                            img_root, category_names=category_names)

    # setup model cfg
    model_yml = args.config_name    # get model .yaml name

    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(
        model_yml))
    cfg.DATASETS.TRAIN = ("ball_train",)
    cfg.DATASETS.TEST = ()
    cfg.DATALOADER.NUM_WORKERS = 2
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
        model_yml)  # Let training initialize from model zoo
    cfg.SOLVER.IMS_PER_BATCH = 2
    cfg.SOLVER.BASE_LR = 0.00025  # pick a good LR
    # 300 iterations seems good enough for this toy dataset; you may need to train longer for a practical dataset
    cfg.SOLVER.MAX_ITER = 1000
    # faster, and good enough for this toy dataset (default: 512)
    # cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # only has 2 class (person & ball)
    cfg.MODEL.RETINANET.NUM_CLASSES = 1

    cfg.merge_from_list(args.opts)  # override using cmd opts option

    # set output dir
    output_dir = os.path.join(
        args.output, model_yml.rstrip('.yaml'))
    cfg.OUTPUT_DIR = f'{output_dir}_lr{cfg.SOLVER.BASE_LR}_iter{cfg.SOLVER.MAX_ITER}'

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=args.resume)
    trainer.train()
