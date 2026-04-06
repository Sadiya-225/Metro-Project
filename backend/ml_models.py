"""
ML Models for Delay Prediction
Implements:
- XGBoost Delay Predictor
- RandomForest baseline
- Context-aware feature engineering
- Stable model persistence and calibrated inference
"""

from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd
import pickle
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


class DelayPredictor:
    def __init__(self, data_dir: Path, model_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir)
        self.model_dir = (
            Path(model_dir)
            if model_dir is not None
            else Path(__file__).resolve().parent / "models"
        )
        self.xgb_model = None
        self.rf_model = None
        self.feature_columns = None
        self.metrics: Dict[str, Dict] = {}
        self.stations = None
        self.delays = None
        self.station_index = None
        self.context_profiles: Dict[str, Dict[Tuple, Dict[str, float]]] = {}

    def load_data(self):
        """Load training data."""
        print("Loading ML training data...")
        self.stations = pd.read_csv(self.data_dir / "station_metadata.csv")
        self.delays = pd.read_csv(self.data_dir / "synthetic_realtime_delays.csv")
        self.station_index = self.stations.set_index("station_id")
        print(f"Loaded {len(self.delays)} delay records")

    def engineer_features(self):
        """Engineer features for ML models."""
        print("Engineering features...")

        data = self.delays.merge(
            self.stations[
                [
                    "station_id",
                    "station_name",
                    "importance_score",
                    "is_interchange",
                    "is_terminal",
                    "commercial_area",
                    "college_zone",
                    "near_it_hub",
                ]
            ],
            on=["station_id", "station_name"],
            how="left",
        )

        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data["hour_sin"] = np.sin(2 * np.pi * data["hour"] / 24)
        data["hour_cos"] = np.cos(2 * np.pi * data["hour"] / 24)

        weather_map = {"clear": 0, "rain": 1, "fog": 2, "storm": 3}
        data["weather_encoded"] = data["weather_factor"].map(weather_map).fillna(0).astype(int)

        for column in [
            "peak_hour",
            "weekday",
            "is_interchange",
            "is_terminal",
            "commercial_area",
            "college_zone",
            "near_it_hub",
        ]:
            data[column] = data[column].fillna(False).astype(int)

        data["importance_score"] = data["importance_score"].fillna(50)
        data["transfer_load"] = data["transfer_load"].fillna(0)
        data["platform_occupancy"] = data["platform_occupancy"].fillna(35)
        data["congestion_score"] = data["congestion_score"].fillna(30)

        self.feature_columns = [
            "hour",
            "hour_sin",
            "hour_cos",
            "peak_hour",
            "weekday",
            "weather_encoded",
            "importance_score",
            "is_interchange",
            "is_terminal",
            "commercial_area",
            "college_zone",
            "near_it_hub",
            "transfer_load",
            "platform_occupancy",
            "congestion_score",
        ]

        X = data[self.feature_columns]
        y = data["delay_minutes"]

        print(f"Features engineered: {len(self.feature_columns)} features")
        return X, y, data

    def train_xgboost(self, X_train, y_train, X_test, y_test):
        """Train XGBoost model."""
        print("Training XGBoost model...")

        self.xgb_model = xgb.XGBRegressor(
            n_estimators=250,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_alpha=0.2,
            reg_lambda=1.5,
            random_state=42,
        )

        self.xgb_model.fit(X_train, y_train)
        y_pred = self.xgb_model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        self.metrics["xgboost"] = {
            "MAE": round(float(mae), 3),
            "RMSE": round(float(rmse), 3),
            "R2": round(float(r2), 3),
        }

        print(f"XGBoost trained - MAE: {mae:.3f}, RMSE: {rmse:.3f}, R2: {r2:.3f}")

    def train_random_forest(self, X_train, y_train, X_test, y_test):
        """Train Random Forest model."""
        print("Training Random Forest model...")

        self.rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=1,
        )

        self.rf_model.fit(X_train, y_train)
        y_pred = self.rf_model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        self.metrics["random_forest"] = {
            "MAE": round(float(mae), 3),
            "RMSE": round(float(rmse), 3),
            "R2": round(float(r2), 3),
        }

        print(f"Random Forest trained - MAE: {mae:.3f}, RMSE: {rmse:.3f}, R2: {r2:.3f}")

    def _build_profile(self, data: pd.DataFrame, group_columns: Iterable[str]):
        grouped = (
            data.groupby(list(group_columns))
            .agg(
                delay_mean=("delay_minutes", "mean"),
                delay_std=("delay_minutes", "std"),
                sample_count=("delay_minutes", "size"),
                transfer_load=("transfer_load", "median"),
                platform_occupancy=("platform_occupancy", "median"),
                congestion_score=("congestion_score", "median"),
            )
            .reset_index()
        )
        grouped["delay_std"] = grouped["delay_std"].fillna(0.0)

        profile = {}
        for row in grouped.to_dict(orient="records"):
            key = tuple(row[column] for column in group_columns)
            profile[key] = {
                "delay_mean": float(row["delay_mean"]),
                "delay_std": float(row["delay_std"]),
                "sample_count": int(row["sample_count"]),
                "transfer_load": float(row["transfer_load"]),
                "platform_occupancy": float(row["platform_occupancy"]),
                "congestion_score": float(row["congestion_score"]),
            }
        return profile

    def _build_context_profiles(self, data: pd.DataFrame):
        self.context_profiles = {
            "exact": self._build_profile(
                data,
                ["station_id", "hour", "peak_hour", "weekday", "weather_factor"],
            ),
            "station_hour_peak_day": self._build_profile(
                data,
                ["station_id", "hour", "peak_hour", "weekday"],
            ),
            "station_hour_day": self._build_profile(
                data,
                ["station_id", "hour", "weekday"],
            ),
            "station_hour": self._build_profile(data, ["station_id", "hour"]),
            "station": self._build_profile(data, ["station_id"]),
        }

    def train(self):
        """Train both models and build inference profiles."""
        X, y, data = self.engineer_features()

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
        )

        print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        self.train_xgboost(X_train, y_train, X_test, y_test)
        self.train_random_forest(X_train, y_train, X_test, y_test)

        self.metrics["feature_importance"] = {
            feature: float(importance)
            for feature, importance in zip(
                self.feature_columns,
                self.xgb_model.feature_importances_,
            )
        }

        self._build_context_profiles(data)

    def save_models(self):
        """Save trained models and metadata."""
        self.model_dir.mkdir(parents=True, exist_ok=True)

        with open(self.model_dir / "xgb_model.pkl", "wb") as file:
            pickle.dump(self.xgb_model, file)

        with open(self.model_dir / "rf_model.pkl", "wb") as file:
            pickle.dump(self.rf_model, file)

        with open(self.model_dir / "feature_columns.pkl", "wb") as file:
            pickle.dump(self.feature_columns, file)

        with open(self.model_dir / "metrics.pkl", "wb") as file:
            pickle.dump(self.metrics, file)

        with open(self.model_dir / "context_profiles.pkl", "wb") as file:
            pickle.dump(self.context_profiles, file)

        print("Models saved")

    def load_models(self):
        """Load pre-trained models and metadata."""
        required_files = [
            self.model_dir / "xgb_model.pkl",
            self.model_dir / "rf_model.pkl",
            self.model_dir / "feature_columns.pkl",
            self.model_dir / "metrics.pkl",
            self.model_dir / "context_profiles.pkl",
        ]

        if not all(path.exists() for path in required_files):
            print("No compatible saved models found")
            return False

        with open(self.model_dir / "xgb_model.pkl", "rb") as file:
            self.xgb_model = pickle.load(file)

        with open(self.model_dir / "rf_model.pkl", "rb") as file:
            self.rf_model = pickle.load(file)

        with open(self.model_dir / "feature_columns.pkl", "rb") as file:
            self.feature_columns = pickle.load(file)

        with open(self.model_dir / "metrics.pkl", "rb") as file:
            self.metrics = pickle.load(file)

        with open(self.model_dir / "context_profiles.pkl", "rb") as file:
            self.context_profiles = pickle.load(file)

        print("Models loaded from disk")
        return True

    def _data_is_newer_than_models(self) -> bool:
        if not self.model_dir.exists():
            return True

        model_files = list(self.model_dir.glob("*.pkl"))
        if not model_files:
            return True

        newest_data_mtime = max(
            (self.data_dir / "station_metadata.csv").stat().st_mtime,
            (self.data_dir / "synthetic_realtime_delays.csv").stat().st_mtime,
        )
        oldest_model_mtime = min(path.stat().st_mtime for path in model_files)
        return newest_data_mtime > oldest_model_mtime

    def load_or_train(self):
        """Load existing models or train new ones."""
        self.load_data()

        if self._data_is_newer_than_models():
            print("Training data changed since the last model build. Retraining...")
            self.train()
            self.save_models()
            return

        if not self.load_models():
            print("Training new models...")
            self.train()
            self.save_models()

    def _get_station_info(self, station_id: str):
        if self.station_index is None or station_id not in self.station_index.index:
            return {
                "importance_score": 50.0,
                "is_interchange": False,
                "is_terminal": False,
                "commercial_area": False,
                "college_zone": False,
                "near_it_hub": False,
            }

        station = self.station_index.loc[station_id]
        return {
            "importance_score": float(station["importance_score"]),
            "is_interchange": bool(station["is_interchange"]),
            "is_terminal": bool(station["is_terminal"]),
            "commercial_area": bool(station["commercial_area"]),
            "college_zone": bool(station["college_zone"]),
            "near_it_hub": bool(station["near_it_hub"]),
        }

    def _get_context_profile(self, features: Dict):
        keys = {
            "exact": (
                features["station_id"],
                features["hour"],
                int(features.get("is_peak", False)),
                int(features.get("weekday", True)),
                features.get("weather", "clear"),
            ),
            "station_hour_peak_day": (
                features["station_id"],
                features["hour"],
                int(features.get("is_peak", False)),
                int(features.get("weekday", True)),
            ),
            "station_hour_day": (
                features["station_id"],
                features["hour"],
                int(features.get("weekday", True)),
            ),
            "station_hour": (features["station_id"], features["hour"]),
            "station": (features["station_id"],),
        }

        for level, key in keys.items():
            profile = self.context_profiles.get(level, {}).get(key)
            if profile:
                return level, profile

        return None, None

    def _estimate_operational_inputs(self, station_info: Dict, features: Dict, profile: Optional[Dict]):
        if profile:
            return {
                "transfer_load": float(profile["transfer_load"]),
                "platform_occupancy": float(profile["platform_occupancy"]),
                "congestion_score": float(profile["congestion_score"]),
            }

        hour = int(features["hour"])
        is_peak = bool(features.get("is_peak", False))
        weekday = bool(features.get("weekday", True))
        weather = features.get("weather", "clear")

        congestion = 24.0
        if is_peak:
            congestion += 18.0
        if weekday:
            congestion += 4.0
        if station_info["is_interchange"]:
            congestion += 16.0
        if station_info["commercial_area"]:
            congestion += 5.0
        if station_info["near_it_hub"] and 17 <= hour <= 20:
            congestion += 8.0
        if station_info["college_zone"] and weekday and (8 <= hour <= 10 or 16 <= hour <= 18):
            congestion += 5.0
        if weather == "rain":
            congestion += 6.0
        elif weather == "fog":
            congestion += 3.0
        elif weather == "storm":
            congestion += 10.0

        congestion = float(np.clip(congestion, 10, 95))

        if station_info["is_interchange"]:
            transfer_load = 12 + (24 if is_peak else 8)
            if weather in {"rain", "storm"}:
                transfer_load += 4
        else:
            transfer_load = 0

        occupancy = float(np.clip(congestion * 0.92 + (6 if station_info["is_terminal"] else 0), 12, 96))

        return {
            "transfer_load": float(transfer_load),
            "platform_occupancy": occupancy,
            "congestion_score": congestion,
        }

    def _rule_based_delay(self, station_info: Dict, features: Dict, operational_inputs: Dict):
        hour = int(features["hour"])
        is_peak = bool(features.get("is_peak", False))
        weekday = bool(features.get("weekday", True))
        weather = features.get("weather", "clear")

        delay = 0.35
        if is_peak:
            delay += 0.9
        if not weekday:
            delay -= 0.2
        if station_info["is_interchange"]:
            delay += 0.95 if is_peak else 0.45
        if station_info["is_terminal"]:
            delay += 0.35 if 6 <= hour <= 10 or 17 <= hour <= 21 else 0.15
        if station_info["commercial_area"] and (is_peak or 12 <= hour <= 15):
            delay += 0.35
        if station_info["college_zone"] and weekday and (8 <= hour <= 10 or 16 <= hour <= 18):
            delay += 0.3
        if station_info["near_it_hub"] and weekday and 17 <= hour <= 20:
            delay += 0.55

        if weather == "rain":
            delay += 0.65
        elif weather == "fog":
            delay += 0.25
        elif weather == "storm":
            delay += 1.4

        delay += max(0.0, operational_inputs["congestion_score"] - 35.0) * 0.015
        delay += max(0.0, operational_inputs["platform_occupancy"] - 60.0) * 0.008
        delay += operational_inputs["transfer_load"] * 0.008

        return float(np.clip(delay, 0.0, 18.0))

    def _estimate_confidence(self, context_level: Optional[str], profile: Optional[Dict]):
        model_r2 = max(float(self.metrics.get("xgboost", {}).get("R2", 0.0)), 0.0)
        base_confidence = 42.0 + model_r2 * 28.0

        level_bonus = {
            "exact": 14.0,
            "station_hour_peak_day": 10.0,
            "station_hour_day": 7.0,
            "station_hour": 5.0,
            "station": 3.0,
            None: 0.0,
        }[context_level]

        support_bonus = 0.0
        variability_penalty = 0.0
        if profile:
            support_bonus = min(profile["sample_count"] * 0.9, 16.0)
            variability_penalty = min(profile["delay_std"] * 2.5, 10.0)

        confidence = base_confidence + level_bonus + support_bonus - variability_penalty
        return float(np.clip(confidence, 35.0, 92.0))

    def predict(self, features: Dict):
        """Predict delay for the given station context."""
        if not self.xgb_model or self.feature_columns is None:
            raise ValueError("Models not trained or loaded")

        weather_map = {"clear": 0, "rain": 1, "fog": 2, "storm": 3}
        station_info = self._get_station_info(features["station_id"])
        context_level, context_profile = self._get_context_profile(features)
        operational_inputs = self._estimate_operational_inputs(
            station_info,
            features,
            context_profile,
        )

        hour = int(features["hour"])
        feature_vector = pd.DataFrame(
            [
                {
                    "hour": hour,
                    "hour_sin": np.sin(2 * np.pi * hour / 24),
                    "hour_cos": np.cos(2 * np.pi * hour / 24),
                    "peak_hour": int(features.get("is_peak", False)),
                    "weekday": int(features.get("weekday", True)),
                    "weather_encoded": weather_map.get(features.get("weather", "clear"), 0),
                    "importance_score": station_info["importance_score"],
                    "is_interchange": int(station_info["is_interchange"]),
                    "is_terminal": int(station_info["is_terminal"]),
                    "commercial_area": int(station_info["commercial_area"]),
                    "college_zone": int(station_info["college_zone"]),
                    "near_it_hub": int(station_info["near_it_hub"]),
                    "transfer_load": operational_inputs["transfer_load"],
                    "platform_occupancy": operational_inputs["platform_occupancy"],
                    "congestion_score": operational_inputs["congestion_score"],
                }
            ]
        )[self.feature_columns]

        model_prediction = float(self.xgb_model.predict(feature_vector)[0])
        context_prediction = (
            float(context_profile["delay_mean"])
            if context_profile
            else self._rule_based_delay(station_info, features, operational_inputs)
        )

        blend_weight = 0.55 if context_profile else 0.3
        prediction = (blend_weight * context_prediction) + ((1 - blend_weight) * model_prediction)
        prediction = float(np.clip(prediction, 0.0, 18.0))

        confidence = self._estimate_confidence(context_level, context_profile)
        return prediction, confidence

    def classify_risk(self, delay_minutes: float) -> str:
        """Classify delay risk level."""
        if delay_minutes < 1.5:
            return "low"
        if delay_minutes < 4.0:
            return "medium"
        if delay_minutes < 7.5:
            return "high"
        return "severe"

    def get_metrics(self):
        """Return model metrics."""
        return self.metrics
