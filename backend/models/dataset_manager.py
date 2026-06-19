"""
Dataset Manager
===============
Manages loading and preprocessing of synthetic, real, and combined datasets
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Literal
from sklearn.model_selection import train_test_split


class DatasetManager:
    """Manages multi-dataset loading and preprocessing."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.synthetic_df = None
        self.real_df = None
        self.feature_columns = None

    def load_synthetic(self) -> pd.DataFrame:
        """Load synthetic Hyderabad metro delay data."""
        try:
            df = pd.read_csv(self.data_dir / "synthetic_realtime_delays.csv")
            print(f"  Loaded {len(df)} synthetic records")
            self.synthetic_df = df
            return df
        except Exception as e:
            print(f"  Error loading synthetic data: {e}")
            return None

    def load_real(self) -> pd.DataFrame:
        """Load real Indian Railway delay data (validated)."""
        try:
            df = pd.read_csv(self.processed_dir / "real_delay_validation.csv")
            print(f"  Loaded {len(df)} real records")
            self.real_df = df
            return df
        except Exception as e:
            print(f"  Error loading real data: {e}")
            return None

    def load_combined(self) -> pd.DataFrame:
        """Load and combine synthetic + real datasets."""
        synthetic = self.load_synthetic()
        real = self.load_real()

        if synthetic is None or real is None:
            print("  Error: Could not load both datasets")
            return None

        # Get common columns
        common_cols = set(synthetic.columns) & set(real.columns)
        common_cols.discard("timestamp")  # Remove timestamp if different format
        common_cols.discard("date")

        # Combine with common columns only
        combined = pd.concat(
            [
                synthetic[list(common_cols)],
                real[list(common_cols)]
            ],
            ignore_index=True
        )

        print(f"  Combined: {len(synthetic)} synthetic + {len(real)} real = {len(combined)} total")
        return combined

    def get_engineered_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features if not already present."""
        if "delay_minutes" not in df.columns:
            if "average_delay_minutes" in df.columns:
                df["delay_minutes"] = df["average_delay_minutes"]
            else:
                print("Warning: Could not find delay column")
                return None

        # Ensure all expected features are present
        # NOTE: Removed congestion_score (calculated from delay info - information leakage)
        expected_features = [
            "hour", "hour_sin", "hour_cos", "peak_hour", "weekday",
            "weather_encoded", "importance_score", "is_interchange",
            "is_terminal", "transfer_load", "platform_occupancy"
        ]

        for feat in expected_features:
            if feat not in df.columns:
                if feat == "hour_sin" and "hour" in df.columns:
                    df[feat] = np.sin(2 * np.pi * df["hour"] / 24)
                elif feat == "hour_cos" and "hour" in df.columns:
                    df[feat] = np.cos(2 * np.pi * df["hour"] / 24)
                elif feat == "peak_hour" and "is_peak" in df.columns:
                    df[feat] = df["is_peak"]
                else:
                    df[feat] = 0

        return df

    def prepare_dataset(
        self,
        dataset_type: Literal["synthetic", "real", "combined"] = "synthetic",
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Load and prepare dataset with train-test split.

        Args:
            dataset_type: "synthetic", "real", or "combined"
            test_size: Test set fraction
            random_state: Random seed

        Returns:
            (X_train, X_test, y_train, y_test)
        """
        print(f"\nPreparing {dataset_type} dataset...")

        # Load appropriate dataset
        if dataset_type == "synthetic":
            df = self.load_synthetic()
        elif dataset_type == "real":
            df = self.load_real()
        elif dataset_type == "combined":
            df = self.load_combined()
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")

        if df is None:
            return None, None, None, None

        # Engineer features
        df = self.get_engineered_features(df)

        # Define feature columns
        # NOTE: Removed congestion_score (calculated from delay info - information leakage)
        feature_cols = [
            "hour", "hour_sin", "hour_cos", "peak_hour", "weekday",
            "weather_encoded", "importance_score", "is_interchange",
            "is_terminal", "transfer_load", "platform_occupancy"
        ]

        # Filter to available columns
        feature_cols = [c for c in feature_cols if c in df.columns]
        self.feature_columns = feature_cols

        # Prepare X and y
        X = df[feature_cols].fillna(0)
        y = df["delay_minutes"]

        # Remove rows with missing targets
        valid_idx = y.notna()
        X = X[valid_idx]
        y = y[valid_idx]

        print(f"  Features: {len(feature_cols)}")
        print(f"  Samples: {len(X)}")
        print(f"  Target mean: {y.mean():.3f} min, std: {y.std():.3f} min")

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state
        )

        print(f"  Train: {len(X_train)}, Test: {len(X_test)}")

        return X_train, X_test, y_train, y_test

    def prepare_cross_domain(
        self,
        train_type: Literal["synthetic", "real"],
        test_type: Literal["synthetic", "real"],
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare cross-domain evaluation: train on one type, test on another.

        Args:
            train_type: Dataset type for training
            test_type: Dataset type for testing
            test_size: Fraction of test data to use
            random_state: Random seed

        Returns:
            (X_train, X_test, y_train, y_test)
        """
        print(f"\nPreparing cross-domain: Train={train_type}, Test={test_type}")

        # Load training data
        if train_type == "synthetic":
            train_df = self.load_synthetic()
        elif train_type == "real":
            train_df = self.load_real()
        else:
            raise ValueError(f"Unknown train dataset: {train_type}")

        # Load test data
        if test_type == "synthetic":
            test_df = self.load_synthetic()
        elif test_type == "real":
            test_df = self.load_real()
        else:
            raise ValueError(f"Unknown test dataset: {test_type}")

        if train_df is None or test_df is None:
            return None, None, None, None

        # Engineer features
        train_df = self.get_engineered_features(train_df)
        test_df = self.get_engineered_features(test_df)

        # Define feature columns
        # NOTE: Removed congestion_score (calculated from delay info - information leakage)
        feature_cols = [
            "hour", "hour_sin", "hour_cos", "peak_hour", "weekday",
            "weather_encoded", "importance_score", "is_interchange",
            "is_terminal", "transfer_load", "platform_occupancy"
        ]

        feature_cols = [c for c in feature_cols if c in train_df.columns and c in test_df.columns]
        self.feature_columns = feature_cols

        # Prepare training data
        X_train = train_df[feature_cols].fillna(0)
        y_train = train_df["delay_minutes"]

        valid_train = y_train.notna()
        X_train = X_train[valid_train]
        y_train = y_train[valid_train]

        # Prepare test data
        X_test = test_df[feature_cols].fillna(0)
        y_test = test_df["delay_minutes"]

        valid_test = y_test.notna()
        X_test = X_test[valid_test]
        y_test = y_test[valid_test]

        # Limit test size if needed
        if test_size < 1.0:
            n_test = int(len(X_test) * test_size)
            X_test = X_test.iloc[:n_test]
            y_test = y_test.iloc[:n_test]

        print(f"  Features: {len(feature_cols)}")
        print(f"  Train: {len(X_train)} {train_type} samples")
        print(f"  Test: {len(X_test)} {test_type} samples")

        return X_train, X_test, y_train, y_test
