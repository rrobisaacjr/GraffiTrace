import detectron2
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg
from dataset_setup import register_datasets  # Ensure datasets are registered
from detectron2.model_zoo import model_zoo

# Register datasets before training
register_datasets()

def setup_cfg():
    """Sets up the Detectron2 configuration for training."""
    cfg = get_cfg()
    cfg.MODEL.DEVICE = "cuda"  # Use "cpu" if no GPU available
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml")
    
    # Dataset and DataLoader
    cfg.DATASETS.TRAIN = ("graffiti_train",)
    cfg.DATASETS.TEST = ("graffiti_validation",)
    cfg.DATALOADER.NUM_WORKERS = 4

    # Solver (Training Parameters)
    cfg.SOLVER.IMS_PER_BATCH = 4  # Increased batch size
    cfg.SOLVER.BASE_LR = 0.0005  # Reduced learning rate
    cfg.SOLVER.MAX_ITER = 10000
    cfg.SOLVER.STEPS = (6000, 8000)  # Added learning rate decay
    cfg.SOLVER.GAMMA = 0.1

    # Model Settings
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # Only one class: graffiti
    cfg.OUTPUT_DIR = "./output"

    return cfg

if __name__ == "__main__":
    cfg = setup_cfg()
    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=False)
    trainer.train()
