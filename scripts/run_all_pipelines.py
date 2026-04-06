"""
Master data pipeline runner.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


def import_module_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main():
    modules = {
        "gtfs": import_module_from_file("gtfs", SCRIPT_DIR / "01_gtfs_ingestion.py"),
        "metadata": import_module_from_file("metadata", SCRIPT_DIR / "02_station_metadata.py"),
        "delays": import_module_from_file("delays", SCRIPT_DIR / "03_synthetic_delays.py"),
        "peak": import_module_from_file("peak", SCRIPT_DIR / "04_peak_hour_labels.py"),
        "transfer": import_module_from_file("transfer", SCRIPT_DIR / "05_transfer_penalty.py"),
        "od": import_module_from_file("od", SCRIPT_DIR / "06_od_benchmarks.py"),
    }

    print("=" * 70)
    print("HYDERABAD METRO - DATA ENGINEERING PIPELINE")
    print("=" * 70)

    steps = [
        ("1/6 GTFS Ingestion", modules["gtfs"].GTFSIngestion),
        ("2/6 Station Metadata", modules["metadata"].StationMetadataGenerator),
        ("3/6 Synthetic Delays", lambda: modules["delays"].SyntheticDelayGenerator(n_samples=50000)),
        ("4/6 Peak Hour Labels", modules["peak"].PeakHourGenerator),
        ("5/6 Transfer Penalty Matrix", modules["transfer"].TransferPenaltyGenerator),
        ("6/6 OD Pair Benchmarks", modules["od"].ODBenchmarkGenerator),
    ]

    for title, factory in steps:
        print(f"\nRunning {title}")
        print("-" * 70)
        factory().run()

    print("\n" + "=" * 70)
    print("All Data Pipelines Completed Successfully")
    print("=" * 70)
    print("Generated Datasets:")
    print("  data/station_metadata.csv")
    print("  data/station_importance_scores.csv")
    print("  data/synthetic_realtime_delays.csv")
    print("  data/peak_hour_labels.csv")
    print("  data/transfer_penalty_matrix.csv")
    print("  data/od_pair_benchmarks.csv")
    print("  data/processed/route_edges.csv")
    print("  data/processed/route_sequences.csv")


if __name__ == "__main__":
    main()
