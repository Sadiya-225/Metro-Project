"""
Multi-Dataset ML Framework
===========================
Modular architecture supporting:
- XGBoost delay predictor
- Random Forest baseline
- LSTM temporal model
- Transformer temporal model

Dataset modes:
- Synthetic: Hyderabad metro synthetic delays
- Real: Indian Railway (etrain) operational data
- Combined: Mixed synthetic + real for robustness
"""

from .base_model import BaseModel
from .dataset_manager import DatasetManager
from .xgboost_model import XGBoostModel
from .random_forest_model import RandomForestModel

__all__ = [
    "BaseModel",
    "DatasetManager",
    "XGBoostModel",
    "RandomForestModel",
]
