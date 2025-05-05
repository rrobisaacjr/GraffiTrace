import torch
import os
import cv2
import numpy as np
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.model_zoo import model_zoo
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

import warnings  # Import warnings

# Suppress Warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def setup_cfg(model_path):
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.WEIGHTS = model_path
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # Only 'graffiti'
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.3
    return cfg

def detect_image(image_path, predictor, metadata, output_dir):
    image = cv2.imread(image_path)
    outputs = predictor(image)
    instances = outputs["instances"].to("cpu")

    num_graffiti_instances = len(instances)
    print(f"{os.path.basename(image_path)} ➜ Detected graffiti instances: {num_graffiti_instances}")

    v = Visualizer(image[:, :, ::-1], metadata=metadata, scale=1.2)
    v = v.draw_instance_predictions(instances)
    result_image = v.get_image()[:, :, ::-1]
    result_image_path = os.path.join(output_dir, os.path.basename(image_path))
    cv2.imwrite(result_image_path, result_image)
    print(f"Result saved to {result_image_path}")


def detect_images_in_directory(image_dir, model_path, output_dir):
    cfg = setup_cfg(model_path)
    predictor = DefaultPredictor(cfg)
    metadata = MetadataCatalog.get("graffiti_train")

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(image_dir):
        if filename.lower().endswith((".jpg", ".png")):
            image_path = os.path.join(image_dir, filename)
            detect_image(image_path, predictor, metadata, output_dir)

if __name__ == "__main__":
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    # ---- USER INPUT ----
    project_directory = r"D:\Downloads\SP\Test"
    model_path = os.path.join(project_directory, "model_final.pth")
    preprocessed_dir = os.path.join(project_directory, "Preprocessed")
    output_dir = os.path.join(project_directory, "detected_images")

    if not os.path.isdir(preprocessed_dir):
        print(f"Preprocessed directory not found at: {preprocessed_dir}")
    else:
        detect_images_in_directory(preprocessed_dir, model_path, output_dir)
