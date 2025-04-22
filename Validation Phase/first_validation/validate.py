import optuna
import torch
import sys
import os
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg
from detectron2.model_zoo import model_zoo
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader

# Get the root directory (graffitrace/)
root_dir = os.path.abspath(os.path.join(__file__, "../../../"))

# Append detectron2_model/ to path
detectron2_model_path = os.path.join(root_dir, "detectron2_model")
sys.path.append(detectron2_model_path)

from dataset_setup import register_datasets

# Make sure the datasets are registered
register_datasets()

def objective(trial):
    cfg = get_cfg()
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml")
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # Only graffiti class

    cfg.DATASETS.TRAIN = ("graffiti_train",)
    cfg.DATASETS.TEST = ("graffiti_validation",)
    cfg.DATALOADER.NUM_WORKERS = 2

    # 🔧 Hyperparameter tuning
    cfg.SOLVER.IMS_PER_BATCH = trial.suggest_categorical("ims_per_batch", [2, 4])
    cfg.SOLVER.ACCUMULATE_GRAD_ITER = trial.suggest_categorical("grad_acc", [1, 2, 4])
    cfg.SOLVER.BASE_LR = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    cfg.SOLVER.MAX_ITER = 2000  # Keep this low for tuning speed
    cfg.SOLVER.STEPS = (1000,)
    cfg.SOLVER.GAMMA = trial.suggest_float("gamma", 0.1, 0.9)
    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = trial.suggest_categorical("roi_batch", [64, 128, 256])

    cfg.OUTPUT_DIR = f"./optuna_output/trial_{trial.number}"
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    # 🚂 Train model
    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=False)
    trainer.train()

    # 🧪 Evaluate model
    evaluator = COCOEvaluator("graffiti_validation", cfg, False, output_dir=cfg.OUTPUT_DIR)
    val_loader = build_detection_test_loader(cfg, "graffiti_validation")
    results = inference_on_dataset(trainer.model, val_loader, evaluator)

    bbox_metrics = results.get("bbox", {})
    precision = bbox_metrics.get("AP", 0.0)          # mAP@[0.50:0.95]
    precision_50 = bbox_metrics.get("AP50", 0.0)     # mAP@0.50
    recall = bbox_metrics.get("AR@100", bbox_metrics.get("AR@10", 0.0))  # fallback

    # You can log all for visibility
    print(f"mAP@[0.50:0.95]: {precision:.3f}")
    print(f"mAP@0.50: {precision_50:.3f}")
    print(f"Recall (AR@100 or fallback): {recall:.3f}")

    # ✅ Log metrics
    trial.set_user_attr("mAP", precision)
    trial.set_user_attr("mAP50", precision_50)
    trial.set_user_attr("Recall", recall)
    trial.set_user_attr("Precision", precision)

    return precision  # mAP@[.50:.95] is your main optimization target


# 🔁 Run the study
if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=15)
    
    # 📄 Save best trial info to a text file
    best_trial = study.best_trial
    summary_path = os.path.join("optuna_output", "best_trial_summary.txt")
    with open(summary_path, "w") as f:
        f.write(f"Best Trial Number: {best_trial.number}\n")
        f.write(f"Value (mAP@[.50:.95]): {best_trial.value:.4f}\n")
        f.write("Hyperparameters:\n")
        for key, value in best_trial.params.items():
            f.write(f"  {key}: {value}\n")
        f.write("Other Metrics:\n")
        for key, value in best_trial.user_attrs.items():
            f.write(f"  {key}: {value}\n")


    print("Best trial:")
    best = study.best_trial
    print(f"  Value (mAP): {best.value}")
    print("  Params: ")
    for key, value in best.params.items():
        print(f"    {key}: {value}")

    print("\nAll Trials Summary:")
    for t in study.trials:
        print(f"Trial {t.number} | mAP: {t.user_attrs.get('mAP'):.3f} | "
              f"mAP50: {t.user_attrs.get('mAP50'):.3f} | "
              f"Recall: {t.user_attrs.get('Recall'):.3f} | "
              f"Precision: {t.user_attrs.get('Precision'):.3f}")
