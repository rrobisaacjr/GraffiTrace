import os
import json
import detectron2
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.structures import BoxMode

def get_graffiti_dicts(split):
    """Loads COCO-formatted dataset for the given split (train/validation)."""
    dataset_dir = os.path.join("datasets", split)
    img_dir = os.path.join(dataset_dir, "images")
    ann_path = os.path.join(dataset_dir, "annotations", f"{split}.json")
    
    # Ensure annotation file exists
    if not os.path.exists(ann_path):
        raise FileNotFoundError(f"Annotation file not found: {ann_path}")
    
    with open(ann_path) as f:
        coco_data = json.load(f)

    image_id_map = {img["id"]: img for img in coco_data.get("images", [])}
    
    dataset_dicts = []
    for img_id, img_info in image_id_map.items():
        image_path = os.path.join(img_dir, img_info["file_name"])

        # Ensure image file exists
        if not os.path.exists(image_path):
            print(f"Warning: Image file not found: {image_path}")
            continue  # Skip missing images

        record = {
            "file_name": image_path,
            "image_id": img_id,
            "height": img_info["height"],
            "width": img_info["width"],
            "annotations": []
        }

        for ann in coco_data.get("annotations", []):
            if ann["image_id"] == img_id:
                corrected_category_id = 0  # Force category_id to 0 for all annotations
                record["annotations"].append({
                    "bbox": ann["bbox"],
                    "bbox_mode": BoxMode.XYWH_ABS,
                    "category_id": corrected_category_id
                })
        
        dataset_dicts.append(record)
    
    return dataset_dicts

def register_datasets():
    """Registers training and validation datasets in Detectron2."""
    for split in ["train", "validation"]:
        dataset_name = f"graffiti_{split}"
        if dataset_name not in DatasetCatalog.list():  # Prevent duplicate registration
            DatasetCatalog.register(dataset_name, lambda split=split: get_graffiti_dicts(split))
            MetadataCatalog.get(dataset_name).set(thing_classes=["graffiti"])

# Automatically register datasets when imported
register_datasets()
