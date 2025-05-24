import os
import shutil
import cv2
import torch
import csv
import numpy as np
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.model_zoo import model_zoo
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
import pandas as pd
import warnings

# Suppress Warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Load the model and prepare the predictor
def setup_cfg(model_path):
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.WEIGHTS = model_path
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.55
    return cfg

# Detect a single image
def detect_image(image_path, predictor, graffiti_metadata, instance_dir, csv_writer, graffiti_id, latitude, longitude, target_place):
    image = cv2.imread(image_path)
    outputs = predictor(image)
    instances = outputs["instances"].to("cpu")

    # Filter instances by confidence score
    mask = instances.scores >= 0.55
    filtered_instances = instances[mask]

    v = Visualizer(image[:, :, ::-1], metadata=graffiti_metadata, scale=1.2)
    v = v.draw_instance_predictions(filtered_instances)  # Use filtered instances
    result_image = v.get_image()[:, :, ::-1]

    num_graffiti_instances = len(filtered_instances) # Use filtered instances

    if num_graffiti_instances > 0: # Only save if graffiti is detected
        result_image_path = os.path.join(instance_dir, f"{graffiti_id}.jpg")
        cv2.imwrite(result_image_path, result_image)
        print(f"\nResult saved to {result_image_path}")
        print(f"\nGraffiti ID: {graffiti_id}")
        print(f"Source File Name: {os.path.basename(image_path)}")
        print(f"Place: {target_place}")
        print(f"Latitude: {latitude}")
        print(f"Longitude: {longitude}")
        print(f"Num Graffiti Instances: {num_graffiti_instances}")

        csv_writer.writerow([
            graffiti_id, os.path.basename(image_path), target_place, latitude, longitude, num_graffiti_instances
        ])
    else:
        print(f"\nNo graffiti detected in {os.path.basename(image_path)}")
    return num_graffiti_instances #return the number of instances

# Process all images
def detect_images_in_directory(image_dir, preprocessed_csv, output_dir, instance_dir, model_path, target_place):
    preprocessed_data = pd.read_csv(preprocessed_csv)
    with open(os.path.join(output_dir, 'results.csv'), mode='w', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([
            "graffiti_id", "source_file_name", "place", "latitude", "longitude", "num_graffiti_instances"
        ])

        cfg = setup_cfg(model_path)
        predictor = DefaultPredictor(cfg)
        graffiti_id = 1

        for _, row in preprocessed_data.iterrows():
            image_name = row['image_name']
            latitude = row['latitude']
            longitude = row['longitude']
            image_path = os.path.join(image_dir, image_name)
            if not os.path.exists(image_path):
                print(f"Warning: Image file not found: {image_path}")
                continue

            num_graffiti_instances = detect_image( # added num_graffiti_instances
                image_path, predictor, MetadataCatalog.get("graffiti_train"),
                instance_dir, csv_writer, f"Graffiti {graffiti_id:05}",
                latitude, longitude, target_place
            )
            if num_graffiti_instances > 0: #increment only if graffiti is detected
                graffiti_id += 1



# Main callable function
def run_graffiti_detection(project_directory, model_path, target_place):
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    image_dir = os.path.join(project_directory, "Preprocessed")
    preprocessed_csv = os.path.join(image_dir, "preprocessed.csv")
    output_dir = os.path.join(project_directory, "results")
    instance_dir = os.path.join(output_dir, "graffiti_instances")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(instance_dir)

    detect_images_in_directory(image_dir, preprocessed_csv, output_dir, instance_dir, model_path, target_place)

# Example call
if __name__ == "__main__":
    project_directory = "C:/Users/MB-PC/Downloads/Test"
    model_path = "C:/Users/MB-PC/Downloads/Test/model_final (1).pth"
    target_place = "Carlos P. Garcia Ave Taguig"
    run_graffiti_detection(project_directory, model_path, target_place)
