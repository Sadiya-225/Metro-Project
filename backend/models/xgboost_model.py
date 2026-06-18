"""
XGBoost Delay Prediction Model
==============================
Production-grade XGBoost model for metro delay prediction
"""

import pickle
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .base_model import BaseModel


class XGBoostModel(BaseModel):
    """XGBoost delay predictor with cross-validation support."""

    def __init__(self, model_dir: Optional[Path] = None):
        super().__init__("XGBoost", model_dir)
        self.model = None

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict:
        """
        Train XGBoost model.

        Args:
            X_train: Training features
            y_train: Training delays

        Returns:
            Training metrics dictionary
        """
        print(f"Training {self.model_name}...")

        self.feature_columns = X_train.columns.tolist()

        # XGBoost hyperparameters (tuned for metro delay prediction)
        self.model = xgb.XGBRegressor(
            n_estimators=250,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_alpha=0.2,
            reg_lambda=1.5,
            random_state=42,
            n_jobs=-1,
        )

        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Generate training metrics
        y_pred_train = self.model.predict(X_train)
        metrics = {
            "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
            "train_rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            "train_r2": float(r2_score(y_train, y_pred_train)),
        }

        self.metrics = metrics
        print(f"  MAE: {metrics['train_mae']:.3f} min")
        print(f"  RMSE: {metrics['train_rmse']:.3f} min")
        print(f"  R2: {metrics['train_r2']:.3f}")

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make delay predictions.

        Args:
            X: Features dataframe

        Returns:
            Predicted delays in minutes
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X)

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        Evaluate model on test set.

        Args:
            X_test: Test features
            y_test: Test delays

        Returns:
            Evaluation metrics
        """
        y_pred = self.predict(X_test)

        metrics = {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2": float(r2_score(y_test, y_pred)),
            "samples": len(y_test),
        }

        print(f"\n{self.model_name} Evaluation:")
        print(f"  MAE: {metrics['mae']:.3f} min")
        print(f"  RMSE: {metrics['rmse']:.3f} min")
        print(f"  R2: {metrics['r2']:.3f}")

        return metrics

    def get_feature_importance(self) -> Dict[str, float]:
        """Get XGBoost feature importance."""
        if not self.is_trained:
            return {}

        importance_dict = self.model.get_booster().get_score(importance_type="weight")
        return importance_dict

    def save(self, filepath: Optional[Path] = None) -> str:
        """Save model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        filepath = filepath or self.model_dir / "xgboost_model.pkl"
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as f:
            pickle.dump(self, f)

        print(f"Model saved to {filepath}")
        return str(filepath)

    def load(self, filepath: Optional[Path] = None) -> bool:
        """Load model from disk."""
        filepath = filepath or self.model_dir / "xgboost_model.pkl"
        filepath = Path(filepath)

        if not filepath.exists():
            print(f"Model file not found: {filepath}")
            return False

        try:
            with open(filepath, "rb") as f:
                loaded = pickle.load(f)

            self.model = loaded.model
            self.feature_columns = loaded.feature_columns
            self.metrics = loaded.metrics
            self.is_trained = True

            print(f"Model loaded from {filepath}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
