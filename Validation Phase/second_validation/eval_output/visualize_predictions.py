# visualize_predictions.py

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import cv2
import random
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.model_zoo import model_zoo
from dataset_setup import register_datasets
from detectron2.data.datasets import load_coco_json

# Step 1: Register datasets
register_datasets()

# Step 2: Setup config with your model
def setup_cfg(model_path):
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # Only graffiti class
    cfg.MODEL.WEIGHTS = model_path
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    cfg.DATASETS.TEST = ("graffiti_validation",)
    return cfg

# Step 3: Visualize predictions
def visualize_predictions(predictor, save_dir="./eval_output/vis_preds/"):
    dataset_dicts = DatasetCatalog.get("graffiti_validation")
    metadata = MetadataCatalog.get("graffiti_validation")
    os.makedirs(save_dir, exist_ok=True)

    for d in dataset_dicts:

        img = cv2.imread(d["file_name"])
        outputs = predictor(img)
        instances = outputs["instances"].to("cpu")
        # Filter out low-confidence predictions
        threshold = 0.5
        high_conf = instances[instances.scores > threshold]

        v = Visualizer(img[:, :, ::-1], metadata=metadata, scale=0.8)
        out = v.draw_instance_predictions(high_conf)

        filename = os.path.basename(d["file_name"])
        save_path = os.path.join(save_dir, f"vis_{filename}")
        cv2.imwrite(save_path, out.get_image()[:, :, ::-1])

if __name__ == "__main__":
    import torch

    model_path = os.path.join(os.path.dirname(__file__), "model_final.pth")
    cfg = setup_cfg(model_path)
    predictor = DefaultPredictor(cfg)

    visualize_predictions(predictor)
    print("✅ Saved predicted visuals in ./eval_output/vis_preds/")
