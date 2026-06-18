"""
Phase 2: Multi-Dataset Training
===============================
Train models on synthetic, real, and combined datasets
Evaluate cross-domain generalization
"""

import json
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from models.dataset_manager import DatasetManager
from models.xgboost_model import XGBoostModel
from models.random_forest_model import RandomForestModel


def train_on_dataset_type(dataset_type: str, data_dir: Path, output_dir: Path):
    """Train both models on a specific dataset type."""
    print("\n" + "=" * 70)
    print(f"TRAINING ON {dataset_type.upper()} DATASET")
    print("=" * 70)

    # Load and prepare dataset
    dm = DatasetManager(data_dir)
    X_train, X_test, y_train, y_test = dm.prepare_dataset(
        dataset_type=dataset_type,
        test_size=0.2,
        random_state=42
    )

    if X_train is None:
        print(f"Could not load {dataset_type} dataset")
        return None

    results = {
        "dataset_type": dataset_type,
        "models": {}
    }

    # Train XGBoost
    xgb_model = XGBoostModel()
    xgb_train_metrics = xgb_model.train(X_train, y_train)
    xgb_eval_metrics = xgb_model.evaluate(X_test, y_test)
    results["models"]["xgboost"] = {
        "train": xgb_train_metrics,
        "test": xgb_eval_metrics
    }

    # Train Random Forest
    rf_model = RandomForestModel()
    rf_train_metrics = rf_model.train(X_train, y_train)
    rf_eval_metrics = rf_model.evaluate(X_test, y_test)
    results["models"]["random_forest"] = {
        "train": rf_train_metrics,
        "test": rf_eval_metrics
    }

    # Save results
    output_file = output_dir / f"training_results_{dataset_type}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")
    return results


def evaluate_cross_domain(data_dir: Path, output_dir: Path):
    """Evaluate models trained on synthetic, tested on real."""
    print("\n" + "=" * 70)
    print("CROSS-DOMAIN EVALUATION: Synthetic -> Real")
    print("=" * 70)

    # Train on synthetic, test on real
    dm = DatasetManager(data_dir)
    X_train, X_test, y_train, y_test = dm.prepare_cross_domain(
        train_type="synthetic",
        test_type="real",
        test_size=1.0,  # Use all real data for testing
        random_state=42
    )

    if X_train is None:
        print("Could not prepare cross-domain datasets")
        return None

    results = {
        "evaluation_type": "synthetic_to_real",
        "train_dataset": "synthetic",
        "test_dataset": "real",
        "models": {}
    }

    # Train XGBoost on synthetic, test on real
    print("\nTraining XGBoost on synthetic data...")
    xgb_model = XGBoostModel()
    xgb_model.train(X_train, y_train)
    xgb_metrics = xgb_model.evaluate(X_test, y_test)
    results["models"]["xgboost"] = xgb_metrics

    # Train Random Forest on synthetic, test on real
    print("\nTraining Random Forest on synthetic data...")
    rf_model = RandomForestModel()
    rf_model.train(X_train, y_train)
    rf_metrics = rf_model.evaluate(X_test, y_test)
    results["models"]["random_forest"] = rf_metrics

    # Save results
    output_file = output_dir / "cross_domain_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nCross-domain results saved to {output_file}")
    return results


def main():
    """Execute Phase 2: Multi-Dataset Training."""
    print("=" * 70)
    print("PHASE 2: MULTI-DATASET ML FRAMEWORK")
    print("=" * 70)

    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    output_dir = data_dir / "processed"
    output_dir.mkdir(exist_ok=True)

    # Train on each dataset type
    results_by_type = {}

    results_by_type["synthetic"] = train_on_dataset_type("synthetic", data_dir, output_dir)
    results_by_type["real"] = train_on_dataset_type("real", data_dir, output_dir)
    results_by_type["combined"] = train_on_dataset_type("combined", data_dir, output_dir)

    # Cross-domain evaluation
    cross_domain_results = evaluate_cross_domain(data_dir, output_dir)

    # Generate summary report
    summary = {
        "phase": "Multi-Dataset Training",
        "dataset_results": results_by_type,
        "cross_domain": cross_domain_results
    }

    summary_file = output_dir / "phase2_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETE: Multi-Dataset Training")
    print("=" * 70)
    print(f"\nAll results saved to: {output_dir}/")


if __name__ == "__main__":
    main()
