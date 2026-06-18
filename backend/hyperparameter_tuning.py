"""
Phase 8: Hyperparameter Optimization
=====================================
Bayesian hyperparameter optimization using Optuna
Tune XGBoost, Random Forest, and other models
"""

import json
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd

try:
    import optuna
    from optuna.pruners import MedianPruner
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("Warning: Optuna not available. Install with: pip install optuna")

from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor


class HyperparameterOptimizer:
    """Optimize hyperparameters using Optuna."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "data" / "processed"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.best_params = {}
        self.optimization_history = {}

    def objective_xgboost(self, trial: optuna.Trial, X_train: pd.DataFrame, y_train: pd.Series) -> float:
        """Objective function for XGBoost optimization."""
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 2.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        }

        model = xgb.XGBRegressor(
            **params,
            random_state=42,
            n_jobs=-1,
            verbose=0
        )

        # Use cross-validation to avoid overfitting to test set
        scores = cross_val_score(
            model, X_train, y_train,
            cv=5,
            scoring='neg_mean_absolute_error'
        )

        return -scores.mean()  # Return MAE (negative because scoring minimizes)

    def objective_random_forest(self, trial: optuna.Trial, X_train: pd.DataFrame, y_train: pd.Series) -> float:
        """Objective function for Random Forest optimization."""
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 5, 30),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
            'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
            'bootstrap': trial.suggest_categorical('bootstrap', [True, False]),
        }

        model = RandomForestRegressor(
            **params,
            random_state=42,
            n_jobs=-1
        )

        scores = cross_val_score(
            model, X_train, y_train,
            cv=5,
            scoring='neg_mean_absolute_error'
        )

        return -scores.mean()

    def optimize_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 100,
        timeout: int = 600
    ) -> Dict:
        """Optimize XGBoost hyperparameters."""
        if not OPTUNA_AVAILABLE:
            print("Optuna not available")
            return {}

        print("\n" + "=" * 70)
        print("PHASE 8: XGBoost Hyperparameter Optimization")
        print("=" * 70)
        print(f"Running {n_trials} trials with timeout {timeout}s...")

        # Create study
        sampler = TPESampler(seed=42)
        pruner = MedianPruner()
        study = optuna.create_study(
            sampler=sampler,
            pruner=pruner,
            direction='minimize'
        )

        # Optimize
        study.optimize(
            lambda trial: self.objective_xgboost(trial, X_train, y_train),
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=True
        )

        # Extract results
        best_trial = study.best_trial
        best_params = best_trial.params
        best_value = best_trial.value

        result = {
            "model": "XGBoost",
            "n_trials": len(study.trials),
            "best_mae": float(best_value),
            "best_params": best_params,
            "study_statistics": {
                "n_complete": len([t for t in study.trials if t.state.name == 'COMPLETE']),
                "n_pruned": len([t for t in study.trials if t.state.name == 'PRUNED']),
                "n_failed": len([t for t in study.trials if t.state.name == 'FAIL']),
            }
        }

        print(f"\nBest MAE: {best_value:.4f} min")
        print(f"Best parameters:")
        for key, value in best_params.items():
            print(f"  {key}: {value}")

        self.best_params['xgboost'] = best_params
        self.optimization_history['xgboost'] = {
            "trials": len(study.trials),
            "best_value": best_value,
            "history": [{"value": t.value, "params": t.params} for t in study.trials]
        }

        return result

    def optimize_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 100,
        timeout: int = 600
    ) -> Dict:
        """Optimize Random Forest hyperparameters."""
        if not OPTUNA_AVAILABLE:
            print("Optuna not available")
            return {}

        print("\n" + "=" * 70)
        print("PHASE 8: Random Forest Hyperparameter Optimization")
        print("=" * 70)
        print(f"Running {n_trials} trials with timeout {timeout}s...")

        sampler = TPESampler(seed=42)
        pruner = MedianPruner()
        study = optuna.create_study(
            sampler=sampler,
            pruner=pruner,
            direction='minimize'
        )

        study.optimize(
            lambda trial: self.objective_random_forest(trial, X_train, y_train),
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=True
        )

        best_trial = study.best_trial
        best_params = best_trial.params
        best_value = best_trial.value

        result = {
            "model": "RandomForest",
            "n_trials": len(study.trials),
            "best_mae": float(best_value),
            "best_params": best_params,
            "study_statistics": {
                "n_complete": len([t for t in study.trials if t.state.name == 'COMPLETE']),
                "n_pruned": len([t for t in study.trials if t.state.name == 'PRUNED']),
                "n_failed": len([t for t in study.trials if t.state.name == 'FAIL']),
            }
        }

        print(f"\nBest MAE: {best_value:.4f} min")
        print(f"Best parameters:")
        for key, value in best_params.items():
            print(f"  {key}: {value}")

        self.best_params['random_forest'] = best_params
        self.optimization_history['random_forest'] = {
            "trials": len(study.trials),
            "best_value": best_value,
            "history": [{"value": t.value, "params": t.params} for t in study.trials]
        }

        return result

    def save_best_params(self) -> Path:
        """Save best hyperparameters to disk."""
        output_file = self.output_dir / "best_hyperparameters.json"

        with open(output_file, "w") as f:
            json.dump(self.best_params, f, indent=2)

        print(f"\nBest hyperparameters saved to {output_file}")
        return output_file

    def generate_tuning_report(self, xgb_result: Dict, rf_result: Dict) -> Dict:
        """Generate comprehensive tuning report."""
        report = {
            "phase": "Hyperparameter Optimization",
            "optimization_results": {
                "xgboost": xgb_result,
                "random_forest": rf_result,
            },
            "key_insights": [
                f"XGBoost best MAE: {xgb_result['best_mae']:.4f} min after {xgb_result['n_trials']} trials",
                f"Random Forest best MAE: {rf_result['best_mae']:.4f} min after {rf_result['n_trials']} trials",
            ],
            "recommendations": [
                f"Use tuned XGBoost with best parameters: {xgb_result['best_params']}",
                f"Use tuned Random Forest with best parameters: {rf_result['best_params']}",
                "Compare tuned models against baseline configurations",
                "Monitor hyperparameter stability across different datasets",
            ]
        }

        return report


if __name__ == "__main__":
    # Example usage
    print("Phase 8: Hyperparameter Optimization requires Optuna")
    print("Install with: pip install optuna")
