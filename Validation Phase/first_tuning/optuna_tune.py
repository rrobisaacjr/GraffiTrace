# optuna_tune.py

import os
import optuna
import torch
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
from detectron2.model_zoo import model_zoo
from dataset_setup import register_datasets

register_datasets()

def build_cfg(trial):
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    cfg.DATASETS.TRAIN = ("graffiti_train",)
    cfg.DATASETS.TEST = ("graffiti_validation",)
    cfg.DATALOADER.FILTER_EMPTY_ANNOTATIONS = False

    # Hyperparameters to optimize
    cfg.SOLVER.BASE_LR = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    cfg.SOLVER.IMS_PER_BATCH = trial.suggest_categorical("ims_per_batch", [2, 4])  # No 8!
    cfg.SOLVER.ACCUMULATE_GRAD_ITER = 1  # (Optional) Remove accumulation to save VRAM
    cfg.SOLVER.MAX_ITER = trial.suggest_int("max_iter", 2000, 10000, step=1000)
    cfg.SOLVER.STEPS = (int(cfg.SOLVER.MAX_ITER * 0.6), int(cfg.SOLVER.MAX_ITER * 0.8))
    cfg.SOLVER.GAMMA = trial.suggest_float("gamma", 0.1, 0.9)

    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml")
    cfg.OUTPUT_DIR = f"./Validation Phase/first_tuning/optuna_output/{trial.number}"
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    return cfg

def objective(trial):
    cfg = build_cfg(trial)

    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=False)
    trainer.train()

    # Evaluate
    evaluator = COCOEvaluator("graffiti_validation", cfg, False, output_dir=cfg.OUTPUT_DIR)
    val_loader = build_detection_test_loader(cfg, "graffiti_validation")
    results = inference_on_dataset(trainer.model, val_loader, evaluator)

    if "bbox" in results:
        ap50 = results["bbox"].get("AP50", 0.0)
        ap = results["bbox"].get("AP", 0.0)
        ar100 = results["bbox"].get("AR@100", 0.0)  # 👉 fixed here!

        return (ap50 + ap + ar100) / 3

    return 0.0


if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=20)

    print("Best trial:")
    print(study.best_trial)
    
    # ✅ Print all trials
    for trial in study.trials:
        print(f"Trial {trial.number}: Params={trial.params}, Score={trial.value}")

    # ✅ Save to CSV
    import pandas as pd
    df = pd.DataFrame([{
        "trial": t.number,
        **t.params,
        "score": t.value
    } for t in study.trials])
    df.to_csv("optuna_trials_results.csv", index=False)

    # ✅ Save the study as a .pkl file (optional backup)
    import pickle
    with open("optuna_study.pkl", "wb") as f:
        pickle.dump(study, f)

    print("✅ Saved all trial results to CSV and pickle.")

