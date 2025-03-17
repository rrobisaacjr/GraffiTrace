if __name__ == "__main__":
    import os
    import json
    import re
    import torch
    import detectron2
    from detectron2.engine import DefaultPredictor
    from detectron2.config import get_cfg
    from detectron2.evaluation import COCOEvaluator, inference_on_dataset
    from detectron2.data import build_detection_test_loader, DatasetCatalog, MetadataCatalog
    from detectron2.model_zoo import model_zoo
    import numpy as np
    from dataset_setup import register_datasets
    
    register_datasets()

    annotation_path = "datasets/validation/annotations/validation.json"
    if not os.path.exists(annotation_path):
        raise FileNotFoundError(f"Annotation file not found: {annotation_path}")

    CHECKPOINT_DIR = "./Training Phase/third_train_output"
    BEST_MODEL_PATH = None
    BEST_MAP = 0

    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    
    cfg.DATASETS.TRAIN = ()
    cfg.DATASETS.TEST = ("graffiti_validation",)
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
    cfg.DATALOADER.NUM_WORKERS = 0
    
    evaluator = COCOEvaluator("graffiti_validation", cfg, False, output_dir="./output/")
    val_loader = build_detection_test_loader(cfg, "graffiti_validation")

    checkpoint_files = sorted([f for f in os.listdir(CHECKPOINT_DIR) if f.endswith(".pth")])
    checkpoints = [(int(re.search(r"model_(\d+).pth", f).group(1)) + 1, os.path.join(CHECKPOINT_DIR, f)) for f in checkpoint_files if re.search(r"model_(\d+).pth", f)]
    checkpoints.sort()

    results = {}

    for iter_num, checkpoint_path in checkpoints:
        print(f"Evaluating checkpoint at {iter_num} iterations...")
        cfg.MODEL.WEIGHTS = checkpoint_path
        predictor = DefaultPredictor(cfg)

        eval_results = inference_on_dataset(predictor.model, val_loader, evaluator)
        bbox_results = eval_results.get("bbox", {})
        
        mAP_50 = bbox_results.get("AP50", float('nan'))
        mAP_50_95 = bbox_results.get("AP", float('nan'))

        results[iter_num] = {
            "mAP@50": mAP_50,
            "mAP@50:95": mAP_50_95
        }

        print(f"  mAP@50: {mAP_50}")
        print(f"  mAP@50:95: {mAP_50_95}")

        if mAP_50_95 > BEST_MAP:
            BEST_MAP = mAP_50_95
            BEST_MODEL_PATH = checkpoint_path

    if BEST_MODEL_PATH:
        print(f"\nBest model found at: {BEST_MODEL_PATH}")
        print(f"Best mAP@50:95: {BEST_MAP}")
    else:
        print("\nNo valid checkpoints found.")

    with open("checkpoint_evaluation.json", "w") as f:
        json.dump(results, f, indent=4)
