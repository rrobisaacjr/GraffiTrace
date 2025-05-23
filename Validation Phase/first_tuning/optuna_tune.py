import os
import optuna
import torch
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
from detectron2.model_zoo import model_zoo
from dataset_setup import register_datasets
import pickle
import pandas as pd
import json
from optuna.storages import RDBStorage
from detectron2.engine import HookBase

# Constants
CSV_LOG_PATH = "optuna_trials_results.csv"

# Register datasets (if needed)
register_datasets()

class OptunaPruningHook(HookBase):
    def __init__(self, trial, eval_period, evaluator, val_loader):
        self.trial = trial
        self.eval_period = eval_period
        self.evaluator = evaluator
        self.val_loader = val_loader

    def after_step(self):
        iter = self.trainer.iter
        if iter % self.eval_period == 0 and iter != 0:
            results = inference_on_dataset(self.trainer.model, self.val_loader, self.evaluator)
            ap50 = results.get("bbox", {}).get("AP50", 0.0)
            self.trial.report(ap50, step=iter)
            if self.trial.should_prune():
                raise optuna.exceptions.TrialPruned()

def build_cfg(trial):
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    cfg.DATASETS.TRAIN = ("graffiti_train",)
    cfg.DATASETS.TEST = ("graffiti_validation",)
    cfg.DATALOADER.FILTER_EMPTY_ANNOTATIONS = False

    cfg.SOLVER.BASE_LR = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    cfg.SOLVER.IMS_PER_BATCH = trial.suggest_categorical("ims_per_batch", [2, 4])
    cfg.SOLVER.ACCUMULATE_GRAD_ITER = 1
    cfg.SOLVER.MAX_ITER = trial.suggest_int("max_iter", 2000, 5000, step=1000)
    cfg.SOLVER.STEPS = (int(cfg.SOLVER.MAX_ITER * 0.6), int(cfg.SOLVER.MAX_ITER * 0.8))
    cfg.SOLVER.GAMMA = trial.suggest_float("gamma", 0.1, 0.9)

    cfg.MODEL.WEIGHTS = os.path.join(os.path.dirname(__file__), "model_final.pth")
    cfg.OUTPUT_DIR = f"./Validation Phase/first_tuning/optuna_output/{trial.number}"
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    # Save trial config
    trial_config_path = os.path.join(cfg.OUTPUT_DIR, "trial_config.json")
    with open(trial_config_path, "w") as f:
        json.dump({
            "lr": cfg.SOLVER.BASE_LR,
            "ims_per_batch": cfg.SOLVER.IMS_PER_BATCH,
            "max_iter": cfg.SOLVER.MAX_ITER,
            "gamma": cfg.SOLVER.GAMMA
        }, f, indent=4)

    return cfg

def objective(trial):
    try:
        cfg = build_cfg(trial)

        evaluator = COCOEvaluator("graffiti_validation", cfg, False, output_dir=cfg.OUTPUT_DIR)
        val_loader = build_detection_test_loader(cfg, "graffiti_validation")

        trainer = DefaultTrainer(cfg)
        trainer.register_hooks([OptunaPruningHook(trial, eval_period=500, evaluator=evaluator, val_loader=val_loader)])
        trainer.resume_or_load(resume=False)
        trainer.train()

        results = inference_on_dataset(trainer.model, val_loader, evaluator)
        
        if "bbox" in results:
            ap50 = results["bbox"].get("AP50", 0.0)
            ap = results["bbox"].get("AP", 0.0)
            ar100 = results["bbox"].get("AR@100", 0.0)

            trial.set_user_attr("AP50", ap50)
            trial.set_user_attr("AP", ap)
            trial.set_user_attr("AR100", ar100)

            score = (ap50 + ap + ar100) / 3

            log_data = {
                "trial": trial.number,
                "lr": cfg.SOLVER.BASE_LR,
                "ims_per_batch": cfg.SOLVER.IMS_PER_BATCH,
                "max_iter": cfg.SOLVER.MAX_ITER,
                "gamma": cfg.SOLVER.GAMMA,
                "AP50": ap50,
                "AP": ap,
                "AR100": ar100,
                "score": score
            }

            df = pd.DataFrame([log_data])
            if not os.path.exists(CSV_LOG_PATH):
                df.to_csv(CSV_LOG_PATH, index=False)
            else:
                df.to_csv(CSV_LOG_PATH, mode='a', header=False, index=False)

            return score

    except optuna.exceptions.TrialPruned:
        print(f"⚠️ Trial {trial.number} was pruned.")
    except RuntimeError as e:
        if "CUDA out of memory" in str(e):
            print(f"⚠️ Trial {trial.number} failed due to OOM.")
        else:
            print(f"⚠️ Trial {trial.number} failed with error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error in trial {trial.number}: {e}")

    return 0.0

if __name__ == "__main__":
    storage = RDBStorage("sqlite:///optuna_study.db")
    study = optuna.create_study(
        direction="maximize",
        study_name="graffiti_tuning",
        storage=storage,
        load_if_exists=True
    )

    study.optimize(objective, n_trials=20)

    print("Best trial:")
    print(study.best_trial)

    with open("optuna_study.pkl", "wb") as f:
        pickle.dump(study, f)

    print("✅ Saved Optuna study.")
