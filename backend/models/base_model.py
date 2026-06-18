"""
Base Model Class
================
Defines interface for all delay prediction models
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd


class BaseModel(ABC):
    """Abstract base class for all delay prediction models."""

    def __init__(self, model_name: str, model_dir: Optional[Path] = None):
        self.model_name = model_name
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).resolve().parent / "checkpoints"
        self.model_dir.mkdir(exist_ok=True)
        self.model = None
        self.feature_columns = None
        self.metrics = {}
        self.is_trained = False

    @abstractmethod
    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict:
        """
        Train the model.

        Args:
            X_train: Training features
            y_train: Training target (delay_minutes)

        Returns:
            Dictionary with training metrics
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Features dataframe

        Returns:
            Array of predicted delay values
        """
        pass

    @abstractmethod
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        Evaluate model performance.

        Args:
            X_test: Test features
            y_test: Test target

        Returns:
            Dictionary with evaluation metrics (MAE, RMSE, R2)
        """
        pass

    @abstractmethod
    def save(self, filepath: Optional[Path] = None) -> str:
        """
        Save model to disk.

        Args:
            filepath: Optional custom filepath

        Returns:
            Path where model was saved
        """
        pass

    @abstractmethod
    def load(self, filepath: Optional[Path] = None) -> bool:
        """
        Load model from disk.

        Args:
            filepath: Optional custom filepath

        Returns:
            True if successful
        """
        pass

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        return {}

    def summary(self) -> Dict:
        """Get model summary."""
        return {
            "model_name": self.model_name,
            "is_trained": self.is_trained,
            "num_features": len(self.feature_columns) if self.feature_columns else 0,
            "metrics": self.metrics,
        }
