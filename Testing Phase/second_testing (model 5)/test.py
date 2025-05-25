import os
import detectron2
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
from detectron2.model_zoo import model_zoo
from dataset_setup import register_datasets

def setup_cfg():
    """Sets up the Detectron2 configuration for testing."""
    cfg = get_cfg()
    cfg.MODEL.DEVICE = "cuda"  # Change to "cpu" if no GPU available
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.WEIGHTS = os.path.join(os.path.dirname(__file__), "best_model.pth")  # Use Optuna-best model
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # Only one class: graffiti

    # Dataset for testing
    cfg.DATASETS.TEST = ("graffiti_test",)
    cfg.DATALOADER.FILTER_EMPTY_ANNOTATIONS = False
    cfg.DATALOADER.NUM_WORKERS = 4

    cfg.OUTPUT_DIR = "./test_output"

    return cfg

if __name__ == "__main__":
    # Register datasets (including test set)
    register_datasets()

    cfg = setup_cfg()

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    
    # Create evaluator and test loader
    evaluator = COCOEvaluator("graffiti_test", cfg, False, output_dir=cfg.OUTPUT_DIR)
    test_loader = build_detection_test_loader(cfg, "graffiti_test")

    # Build predictor and run evaluation
    predictor = DefaultPredictor(cfg)
    results = inference_on_dataset(predictor.model, test_loader, evaluator)

    print("Evaluation results:", results)
