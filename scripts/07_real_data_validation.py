"""
Phase 1: Real Data Validation Pipeline
========================================
Load real-world Indian train delay data from etrain_delays.csv
Map to unified metro delay prediction format
Generate validation dataset for cross-domain evaluation

Output:
- data/processed/real_delay_validation.csv
- data/processed/validation_report.json
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, List


class RealDataValidator:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        self.raw_delays = None
        self.processed_delays = None
        self.validation_report = {}

    def load_real_delays(self):
        """Load etrain_delays.csv with real operational data."""
        try:
            self.raw_delays = pd.read_csv(self.data_dir / "etrain_delays.csv")
            print(f"[OK] Loaded {len(self.raw_delays)} records")
            print(f"  Columns: {list(self.raw_delays.columns)}")
            print(f"  Date range: {self.raw_delays['scraped_at'].min()} to {self.raw_delays['scraped_at'].max()}")
            return True
        except Exception as e:
            print(f"[ERROR] Error loading data: {e}")
            return False

    def infer_schema(self) -> Dict:
        """Automatically infer schema from raw delays."""
        print("\nInferring schema from real delay data...")
        schema = {
            "source": "etrain_delays.csv (Indian Railways)",
            "total_records": len(self.raw_delays),
            "unique_trains": self.raw_delays["train_number"].nunique(),
            "unique_stations": self.raw_delays["station_code"].nunique(),
            "unique_station_names": self.raw_delays["station_name"].nunique(),
            "columns": {
                col: {
                    "type": str(self.raw_delays[col].dtype),
                    "nulls": int(self.raw_delays[col].isna().sum()),
                    "unique_values": self.raw_delays[col].nunique() if col != "average_delay_minutes" else "N/A"
                }
                for col in self.raw_delays.columns
            },
            "delay_stats": {
                "mean": float(self.raw_delays["average_delay_minutes"].mean()),
                "median": float(self.raw_delays["average_delay_minutes"].median()),
                "std": float(self.raw_delays["average_delay_minutes"].std()),
                "min": float(self.raw_delays["average_delay_minutes"].min()),
                "max": float(self.raw_delays["average_delay_minutes"].max()),
                "q25": float(self.raw_delays["average_delay_minutes"].quantile(0.25)),
                "q75": float(self.raw_delays["average_delay_minutes"].quantile(0.75))
            }
        }

        print(f"  Train numbers: {schema['unique_trains']}")
        print(f"  Stations: {schema['unique_stations']}")
        print(f"  Delay mean: {schema['delay_stats']['mean']:.2f} min")
        print(f"  Delay range: {schema['delay_stats']['min']:.2f} - {schema['delay_stats']['max']:.2f} min")

        return schema

    def engineer_features(self) -> pd.DataFrame:
        """Engineer unified delay features from real railway data."""
        print("\nEngineering features from real delay data...")

        df = self.raw_delays.copy()

        # 1. Parse timestamp
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True)
        df["date"] = df["scraped_at"].dt.date
        df["hour"] = df["scraped_at"].dt.hour
        df["day_of_week"] = df["scraped_at"].dt.dayofweek
        df["month"] = df["scraped_at"].dt.month

        # 2. Extract peak hour indicator
        # Peak hours: morning (6-10) and evening (17-21)
        df["is_peak_morning"] = df["hour"].isin([6, 7, 8, 9, 10]).astype(int)
        df["is_peak_evening"] = df["hour"].isin([17, 18, 19, 20, 21]).astype(int)
        df["is_peak"] = (df["is_peak_morning"] | df["is_peak_evening"]).astype(int)

        # 3. Day features
        df["is_weekday"] = (df["day_of_week"] < 5).astype(int)
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

        # 4. Derive operational features from percentage columns
        # Categorize reliability levels based on percentage right-time
        df["reliability_score"] = df["pct_right_time"]
        df["slight_delay_pct"] = df["pct_slight_delay"]
        df["significant_delay_pct"] = df["pct_significant_delay"]
        df["cancellation_pct"] = df["pct_cancelled_unknown"]

        # 5. Create synthetic operational features based on percentages
        # These simulate platform occupancy, congestion, weather factors
        df["platform_occupancy"] = df["pct_slight_delay"] + df["pct_significant_delay"]
        df["platform_occupancy"] = np.minimum(df["platform_occupancy"], 100)  # Cap at 100

        # Congestion score correlates with delay percentage
        df["congestion_score"] = df["significant_delay_pct"] * 0.5 + df["cancellation_pct"] * 0.5

        # Weather inference: higher cancellation rates suggest adverse weather
        df["weather_factor"] = np.where(
            df["cancellation_pct"] > 5,
            "storm",
            np.where(df["slight_delay_pct"] > 30, "rain", "clear")
        )
        weather_map = {"clear": 0, "rain": 1, "fog": 2, "storm": 3}
        df["weather_encoded"] = df["weather_factor"].map(weather_map)

        # 6. Station features (simulated)
        # Assign importance based on traffic volume and delay patterns
        station_importance = df.groupby("station_code").agg({
            "average_delay_minutes": ["mean", "count"]
        }).reset_index()
        station_importance.columns = ["station_code", "avg_delay", "frequency"]

        # Normalize importance score (0-100)
        station_importance["importance_score"] = (
            (station_importance["avg_delay"] / station_importance["avg_delay"].max()) * 40 +
            (station_importance["frequency"] / station_importance["frequency"].max()) * 60
        )

        df = df.merge(
            station_importance[["station_code", "importance_score"]],
            on="station_code"
        )

        # 7. Add engineered temporal features
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

        # 8. Transfer and connectivity features (simulated)
        df["transfer_load"] = df["platform_occupancy"] * 0.3  # Transfer load correlates with occupancy
        df["is_interchange"] = 0  # Mark as 0 (no interchange info in this dataset)
        df["is_terminal"] = 0
        df["connectivity_score"] = 50 + df["importance_score"] * 0.5

        # 9. Route features
        df["route_complexity"] = df.groupby("train_number")["station_code"].transform("count")
        df["route_complexity"] = np.minimum(df["route_complexity"], 100)

        # Normalize all feature columns
        print("  Normalizing features...")
        for col in ["platform_occupancy", "congestion_score", "transfer_load"]:
            df[col] = np.maximum(0, np.minimum(100, df[col]))

        print(f"  [OK] Engineered {len(df)} records with {len(self.get_feature_columns())} features")

        self.processed_delays = df
        return df

    def get_feature_columns(self) -> List[str]:
        """Return list of engineered feature columns."""
        return [
            "hour", "hour_sin", "hour_cos",
            "day_of_week", "month", "is_peak", "is_weekday",
            "importance_score", "is_interchange", "is_terminal",
            "transfer_load", "platform_occupancy", "congestion_score",
            "weather_encoded", "reliability_score", "connectivity_score",
            "route_complexity", "station_code", "train_number",
            "average_delay_minutes"  # Target variable
        ]

    def create_validation_dataset(self) -> pd.DataFrame:
        """Create clean validation dataset with standardized format."""
        print("\nCreating standardized validation dataset...")

        features = self.get_feature_columns()

        # Filter to available columns
        available_features = [f for f in features if f in self.processed_delays.columns]
        validation_df = self.processed_delays[available_features].copy()

        # Rename target to match metro convention
        validation_df["delay_minutes"] = validation_df["average_delay_minutes"]
        validation_df = validation_df.drop(columns=["average_delay_minutes"])

        # Remove any rows with critical missing values
        validation_df = validation_df.dropna(subset=["delay_minutes"])
        validation_df = validation_df.fillna(0)

        print(f"  [OK] Created validation dataset: {len(validation_df)} rows")

        return validation_df

    def generate_validation_report(self, schema: Dict, validation_df: pd.DataFrame) -> Dict:
        """Generate comprehensive validation report."""
        print("\nGenerating validation report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "dataset_source": "etrain_delays.csv (Indian Railways Historical Data)",
            "schema_inference": schema,
            "data_quality": {
                "total_records": len(validation_df),
                "features_engineered": len([c for c in validation_df.columns if c != "delay_minutes"]),
                "missing_values": int(validation_df.isna().sum().sum()),
                "duplicates": int(validation_df.duplicated().sum()),
                "trains": validation_df["train_number"].nunique() if "train_number" in validation_df.columns else 0,
                "stations": validation_df["station_code"].nunique() if "station_code" in validation_df.columns else 0,
            },
            "delay_statistics": {
                "mean_delay_minutes": float(validation_df["delay_minutes"].mean()),
                "median_delay_minutes": float(validation_df["delay_minutes"].median()),
                "std_delay_minutes": float(validation_df["delay_minutes"].std()),
                "min_delay_minutes": float(validation_df["delay_minutes"].min()),
                "max_delay_minutes": float(validation_df["delay_minutes"].max()),
                "q25_delay_minutes": float(validation_df["delay_minutes"].quantile(0.25)),
                "q75_delay_minutes": float(validation_df["delay_minutes"].quantile(0.75)),
            },
            "feature_coverage": {
                "peak_hour_records": int((validation_df["is_peak"] == 1).sum()),
                "weekday_records": int((validation_df["is_weekday"] == 1).sum()),
                "stations_in_dataset": validation_df["station_code"].nunique() if "station_code" in validation_df.columns else 0,
            },
            "cross_domain_notes": {
                "source_domain": "Indian Railways (multiple routes, all-India data)",
                "target_domain": "Hyderabad Metro (57 stations, 3 lines)",
                "domain_shift_factors": [
                    "Different transportation modes (trains vs metro)",
                    "Different network sizes (100+ stations vs 57 stations)",
                    "Different peak hour patterns",
                    "Different weather impact (long-haul trains vs metro)"
                ],
                "validation_purpose": "Evaluate model generalization to out-of-distribution transit data",
                "expected_use": "Train-Synthetic → Test-Real (cross-domain evaluation)"
            },
            "recommendations": [
                "Use for cross-domain generalization testing",
                "Compare synthetic-trained models on real railway data",
                "Evaluate feature importance transfer across domains",
                "Assess model robustness to different transit systems"
            ]
        }

        self.validation_report = report
        return report

    def save_outputs(self, validation_df: pd.DataFrame, report: Dict):
        """Save processed data and report to disk."""
        print("\nSaving outputs...")

        # Save validation dataset
        csv_path = self.processed_dir / "real_delay_validation.csv"
        validation_df.to_csv(csv_path, index=False)
        print(f"  [OK] Saved validation dataset: {csv_path}")

        # Save validation report
        report_path = self.processed_dir / "validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"  [OK] Saved validation report: {report_path}")

        # Save feature summary
        feature_summary = {
            "features": self.get_feature_columns(),
            "target_variable": "delay_minutes",
            "total_features": len(self.get_feature_columns()) - 1,  # Exclude target
            "feature_types": {
                "temporal": ["hour", "hour_sin", "hour_cos", "day_of_week", "month", "is_peak", "is_weekday"],
                "operational": ["platform_occupancy", "congestion_score", "transfer_load", "weather_encoded"],
                "station": ["importance_score", "is_interchange", "is_terminal", "connectivity_score"],
                "route": ["route_complexity"],
                "identifiers": ["station_code", "train_number"]
            }
        }

        features_path = self.processed_dir / "real_delay_features.json"
        with open(features_path, "w") as f:
            json.dump(feature_summary, f, indent=2)
        print(f"  [OK] Saved feature summary: {features_path}")

    def run(self):
        """Execute full real data validation pipeline."""
        print("=" * 70)
        print("PHASE 1: REAL DATA VALIDATION PIPELINE")
        print("=" * 70)

        # Step 1: Load data
        if not self.load_real_delays():
            return False

        # Step 2: Infer schema
        schema = self.infer_schema()

        # Step 3: Engineer features
        self.engineer_features()

        # Step 4: Create validation dataset
        validation_df = self.create_validation_dataset()

        # Step 5: Generate report
        report = self.generate_validation_report(schema, validation_df)

        # Step 6: Save outputs
        self.save_outputs(validation_df, report)

        print("\n" + "=" * 70)
        print("[OK] PHASE 1 COMPLETE: Real data validation pipeline executed")
        print("=" * 70)
        print(f"\nOutputs:")
        print(f"  - {self.processed_dir}/real_delay_validation.csv")
        print(f"  - {self.processed_dir}/validation_report.json")
        print(f"  - {self.processed_dir}/real_delay_features.json")

        return True


if __name__ == "__main__":
    import sys

    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"

    validator = RealDataValidator(data_dir)
    success = validator.run()
    sys.exit(0 if success else 1)
