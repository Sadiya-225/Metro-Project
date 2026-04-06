"""
FastAPI backend for the Metro Route Intelligence dashboard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ml_models import DelayPredictor
from route_engine import MetroRouteEngine

app = FastAPI(
    title="Metro Route Intelligence API",
    description="Data-driven route optimization, congestion analytics, and delay prediction",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
MODELS_DIR = BACKEND_DIR / "models"

route_engine = None
delay_predictor = None


def _json_safe_records(frame: pd.DataFrame) -> List[Dict]:
    safe_frame = frame.replace([np.inf, -np.inf], np.nan)
    safe_frame = safe_frame.astype(object).where(pd.notnull(safe_frame), None)
    return safe_frame.to_dict(orient="records")


class RouteRequest(BaseModel):
    source: str
    destination: str
    algorithm: str = "dijkstra"
    k_paths: int = 3


class DelayPredictionRequest(BaseModel):
    station_id: str
    hour: int
    is_peak: bool
    weekday: bool
    weather: str = "clear"


@app.on_event("startup")
async def startup_event():
    global route_engine, delay_predictor

    print("Initializing Metro Route Intelligence Backend...")
    route_engine = MetroRouteEngine(DATA_DIR)
    route_engine.build_graph()
    print("Route engine initialized")

    delay_predictor = DelayPredictor(DATA_DIR, MODELS_DIR)
    delay_predictor.load_or_train()
    print("ML predictor initialized")
    print("Backend ready")


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Metro Route Intelligence API",
        "version": "2.0.0",
    }


@app.get("/api/stations")
async def get_stations():
    try:
        stations = pd.read_csv(DATA_DIR / "station_metadata.csv")
        return {
            "count": len(stations),
            "stations": _json_safe_records(stations),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/stations/importance")
async def get_station_importance():
    try:
        importance_scores = pd.read_csv(DATA_DIR / "station_importance_scores.csv")
        return {
            "count": len(importance_scores),
            "stations": _json_safe_records(importance_scores),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/route/optimize")
async def optimize_route(request: RouteRequest):
    try:
        if route_engine is None:
            raise HTTPException(status_code=503, detail="Route engine not initialized")

        analysis = route_engine.get_route_analysis(
            request.source,
            request.destination,
            algorithm=request.algorithm,
            k_paths=request.k_paths,
        )
        if not analysis["shortest_path"]:
            raise HTTPException(
                status_code=404,
                detail=f"No route found between {request.source} and {request.destination}",
            )
        return analysis
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/predict/delay")
async def predict_delay(request: DelayPredictionRequest):
    try:
        if delay_predictor is None:
            raise HTTPException(status_code=503, detail="ML predictor not initialized")

        predicted_delay, confidence = delay_predictor.predict(
            {
                "station_id": request.station_id,
                "hour": request.hour,
                "is_peak": request.is_peak,
                "weekday": request.weekday,
                "weather": request.weather,
            }
        )
        return {
            "station_id": request.station_id,
            "predicted_delay": round(predicted_delay, 2),
            "confidence": round(confidence, 2),
            "risk_level": delay_predictor.classify_risk(predicted_delay),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/bottlenecks")
async def get_bottlenecks(limit: int = 10):
    try:
        bottlenecks = route_engine.get_top_bottlenecks(limit=limit)
        return {"count": len(bottlenecks), "bottlenecks": bottlenecks}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    try:
        return route_engine.get_dashboard_analytics()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/delays/stats")
async def get_delay_stats():
    try:
        delays = pd.read_csv(DATA_DIR / "synthetic_realtime_delays.csv")
        hourly = (
            delays.groupby("hour")["delay_minutes"]
            .mean()
            .round(2)
            .to_dict()
        )
        return {
            "overall": {
                "mean": round(float(delays["delay_minutes"].mean()), 2),
                "median": round(float(delays["delay_minutes"].median()), 2),
                "max": round(float(delays["delay_minutes"].max()), 2),
                "std": round(float(delays["delay_minutes"].std()), 2),
            },
            "by_peak": {
                str(key): round(float(value), 2)
                for key, value in delays.groupby("peak_hour")["delay_minutes"].mean().to_dict().items()
            },
            "by_station": {
                key: round(float(value), 2)
                for key, value in delays.groupby("station_name")["delay_minutes"].mean().to_dict().items()
            },
            "by_hour": hourly,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/od-pairs")
async def get_od_benchmarks(limit: int = 20):
    try:
        od_pairs = pd.read_csv(DATA_DIR / "od_pair_benchmarks.csv")
        inefficient = od_pairs.sort_values("inefficiency_ratio", ascending=False).head(limit)
        return {
            "count": len(od_pairs),
            "inefficient_routes": _json_safe_records(inefficient),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/ml/metrics")
async def get_ml_metrics():
    try:
        if delay_predictor is None:
            raise HTTPException(status_code=503, detail="ML predictor not initialized")
        return delay_predictor.get_metrics()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/upload/gtfs")
async def upload_gtfs(files: List = None):
    gtfs_dir = PROJECT_DIR / "public" / "gtfs_hmrl"
    return {
        "status": "success" if gtfs_dir.exists() else "info",
        "message": "GTFS files already present" if gtfs_dir.exists() else "Use manual upload or existing files",
        "files": [file.name for file in gtfs_dir.glob("*.txt")] if gtfs_dir.exists() else [],
    }


@app.post("/api/upload/osm")
async def upload_osm(file=None):
    osm_file = PROJECT_DIR / "public" / "export.geojson"
    return {
        "status": "success" if osm_file.exists() else "info",
        "message": "OSM file already present" if osm_file.exists() else "Use manual upload or existing file",
        "file": str(osm_file) if osm_file.exists() else None,
    }


@app.post("/api/generate/step{step_num}")
async def generate_data_step(step_num: int):
    import subprocess
    import sys

    script_map = {
        1: PROJECT_DIR / "scripts" / "01_gtfs_ingestion.py",
        2: PROJECT_DIR / "scripts" / "02_station_metadata.py",
        3: PROJECT_DIR / "scripts" / "03_synthetic_delays.py",
        4: PROJECT_DIR / "scripts" / "04_peak_hour_labels.py",
        5: PROJECT_DIR / "scripts" / "05_transfer_penalty.py",
        6: PROJECT_DIR / "scripts" / "06_od_benchmarks.py",
    }

    if step_num not in script_map:
        raise HTTPException(status_code=400, detail="Invalid step number")

    try:
        script_path = script_map[step_num]
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(script_path.parent),
        )
        if result.returncode == 0:
            return {
                "status": "success",
                "message": f"Step {step_num} Completed Successfully",
                "output": result.stdout,
            }
        return {"status": "error", "error": result.stderr or "Script failed"}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Script execution timeout")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
