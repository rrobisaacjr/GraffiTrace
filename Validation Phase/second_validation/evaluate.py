# evaluate.py

import os
import torch
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
from detectron2.model_zoo import model_zoo
from dataset_setup import register_datasets

import contextlib

# Ensure datasets are registered
register_datasets()

def setup_cfg(model_path):
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # only 1 class: graffiti
    cfg.MODEL.WEIGHTS = model_path
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    cfg.DATASETS.TEST = ("graffiti_validation",)
    cfg.DATALOADER.FILTER_EMPTY_ANNOTATIONS = False
    return cfg

if __name__ == "__main__":
    
    # Path to your trained model
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_pth = os.path.join(script_dir, "model_final.pth")

    cfg = setup_cfg(model_pth)
    predictor = DefaultPredictor(cfg)

    evaluator = COCOEvaluator("graffiti_validation", cfg, False, output_dir="./eval_output/")
    val_loader = build_detection_test_loader(cfg, "graffiti_validation")
    
    print("Running evaluation...")
    results = inference_on_dataset(predictor.model, val_loader, evaluator)
    print("Evaluation results:\n", results)
    
    output_path = "./eval_output/metrics.txt"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Run the evaluation first
    results = inference_on_dataset(predictor.model, val_loader, evaluator)

    # Then write everything (including recall) to file
    with open(output_path, "w") as f, contextlib.redirect_stdout(f):
        print("Running evaluation...")
        print("Evaluation results:\n", results)

        if "bbox" in results:
            bbox_metrics = results["bbox"]
            print("\n--- Key Evaluation Metrics ---")
            print(f"Average Precision (AP): {bbox_metrics['AP']:.4f}")
            print(f"AP at IoU=0.50 (AP50): {bbox_metrics['AP50']:.4f}")
            print(f"AP at IoU=0.75 (AP75): {bbox_metrics['AP75']:.4f}")

            if hasattr(evaluator, "coco_eval") and evaluator.coco_eval is not None:
                coco_eval_stats = evaluator.coco_eval["bbox"].stats
                ar100 = coco_eval_stats[8]  # AR@100
                print(f"Average Recall (AR@100): {ar100:.4f}")



