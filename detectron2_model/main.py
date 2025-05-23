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
    cfg.DATALOADER.FILTER_EMPTY_ANNOTATIONS = False
    
    # Dataset and DataLoader
    cfg.DATASETS.TRAIN = ("graffiti_train",)
    cfg.DATASETS.TEST = ("graffiti_validation",)
    cfg.DATALOADER.NUM_WORKERS = 4

    # Solver (Training Parameters) - Updated with Lower Learning Rate
    cfg.SOLVER.IMS_PER_BATCH = 4  # Keep batch size (VRAM limit)
    cfg.SOLVER.ACCUMULATE_GRAD_ITER = 4  # Simulating batch size 16 for better convergence
    cfg.SOLVER.BASE_LR = 0.0001  # Lower learning rate for smoother convergence (adjust as needed)
    cfg.SOLVER.MAX_ITER = 10000
    cfg.SOLVER.STEPS = (3000, 6000)  # Earlier decay for smoother learning
    cfg.SOLVER.GAMMA = 0.5  # Less aggressive LR decay
    cfg.SOLVER.CHECKPOINT_PERIOD = 2000
    

    # Model Settings
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # Only one class: graffiti
    cfg.OUTPUT_DIR = "./fourth_train_output"

    return cfg

if __name__ == "__main__":
    cfg = setup_cfg()
    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=False)
    trainer.train()
