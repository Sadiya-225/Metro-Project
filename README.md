# 🚇 Metro Route Intelligence Dashboard

**Project Title:** Shortest Path vs Real Time in Public Transport System
**Student:** Ms. SADIYA MAHEEN SIDDIQUI
**Category:** Optimization
**Submission Deadline:** 15th April 2026

---

## 📋 Project Overview

An AI-powered metro route intelligence dashboard that provides:
- **Shortest Path Optimization** using Dijkstra, A*, and Yen's K-shortest paths algorithms
- **Real-time ETA Deviation Analysis** comparing ideal vs actual travel times
- **Bottleneck Station Intelligence** identifying congestion hotspots
- **ML-based Delay Prediction** using XGBoost and Random Forest models
- **Interactive Route Visualization** with MapLibre GL

---

## 🏗️ Architecture

```
metro-project/
├── backend/              # FastAPI backend
│   ├── main.py          # API endpoints
│   ├── route_engine.py  # Graph algorithms (Dijkstra, A*, Yen)
│   ├── ml_models.py     # XGBoost & RandomForest models
│   └── requirements.txt # Python dependencies
│
├── scripts/             # Data engineering pipeline
│   ├── 01_gtfs_ingestion.py         # GTFS & OSM data parsing
│   ├── 02_station_metadata.py       # Station importance scoring
│   ├── 03_synthetic_delays.py       # Delay dataset generation (50K records)
│   ├── 04_peak_hour_labels.py       # Peak hour classification
│   ├── 05_transfer_penalty.py       # Transfer cost matrix
│   ├── 06_od_benchmarks.py          # OD pair analysis
│   └── run_all_pipelines.py         # Master execution script
│
├── app/                 # Next.js App Router
│   ├── page.tsx        # Route Intelligence page
│   ├── bottlenecks/    # Bottleneck Analytics dashboard
│   └── ml-prediction/  # ML Prediction interface
│
├── data/                # Generated datasets (created by scripts)
│   ├── station_metadata.csv
│   ├── synthetic_realtime_delays.csv (50,000 records)
│   ├── peak_hour_labels.csv
│   ├── transfer_penalty_matrix.csv
│   └── od_pair_benchmarks.csv
│
└── public/              # Static assets
    ├── gtfs_hmrl/      # GTFS feeds (stops, routes, trips, etc.)
    └── export.geojson  # OpenStreetMap station data
```

---

## ⚙️ Tech Stack

### Backend
- **FastAPI** - High-performance Python API framework
- **NetworkX** - Graph algorithms (Dijkstra, A*, Yen)
- **XGBoost & Random Forest** - ML delay prediction
- **Pandas & NumPy** - Data processing

### Frontend
- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **MapLibre GL** - Interactive map visualization
- **Recharts** - Data visualization charts
- **Framer Motion** - Smooth animations

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Step 1: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Generate Datasets (PHASE 1)

```bash
# From project root
cd scripts
python run_all_pipelines.py
```

This will generate all required datasets:
- ✅ GTFS ingestion & station mapping
- ✅ Station metadata with importance scores
- ✅ 50,000 synthetic delay records
- ✅ Peak hour labels
- ✅ Transfer penalty matrix
- ✅ OD pair benchmarks

**Estimated time:** 2-3 minutes

### Step 3: Start Backend Server

```bash
cd backend
python main.py
```

Backend will start at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Step 4: Install Frontend Dependencies

```bash
# From project root
npm install --legacy-peer-deps
```

### Step 5: Start Frontend

```bash
npm run dev
```

Frontend will start at: `http://localhost:3000`

---

## 📊 Generated Datasets

### 1. `station_metadata.csv`
Complete station information including:
- Station ID, name, coordinates
- Line assignments (Red, Blue, Green)
- Interchange & terminal flags
- Importance scores (0-100)
- Zone classification (IT Hub, Commercial, Educational, etc.)
- Smart city priority markers

### 2. `synthetic_realtime_delays.csv` (50,000 records)
Realistic delay patterns with:
- Timestamp, station, delay duration
- Peak hour indicators
- Weather factors (clear, rain, fog, storm)
- Transfer load & platform occupancy
- Congestion scores

### 3. `peak_hour_labels.csv`
Hourly peak classifications:
- Morning office rush (8-10 AM)
- Evening return rush (5-8 PM)
- Weekend market hours
- Student rush periods
- Expected wait multipliers

### 4. `transfer_penalty_matrix.csv`
Walking time & penalties between stations:
- Walking distance & time
- Crowd penalties at interchanges
- Platform switch costs
- Escalator delays
- Effective transfer costs

### 5. `od_pair_benchmarks.csv`
Origin-Destination analysis:
- Shortest path time vs scheduled time
- Actual delay time & inefficiency ratios
- Bottleneck station identification
- Transfer counts

---

## 🎯 API Endpoints

### Route Optimization
```http
POST /api/route/optimize
Content-Type: application/json

{
  "source": "Ameerpet",
  "destination": "Nagole",
  "algorithm": "dijkstra",
  "k_paths": 3
}
```

### Delay Prediction
```http
POST /api/predict/delay
Content-Type: application/json

{
  "station_id": "AME",
  "hour": 18,
  "is_peak": true,
  "weekday": true,
  "weather": "rain"
}
```

### Bottleneck Analysis
```http
GET /api/bottlenecks?limit=10
```

### ML Model Metrics
```http
GET /api/ml/metrics
```

---

## 🧠 ML Models

### XGBoost Delay Predictor
- **Features:** 15 engineered features
- **Training:** 80/20 train-test split on 50K records
- **Metrics:** MAE, RMSE, R² score
- **Output:** Delay prediction in minutes + confidence

### Random Forest Ensemble
- **Purpose:** Comparison baseline & ensemble voting
- **Configuration:** 100 trees, max depth 10

---

## 🔬 Algorithms Implemented

### 1. Dijkstra's Algorithm
- **Purpose:** Shortest path optimization
- **Complexity:** O((V + E) log V)

### 2. A* Algorithm
- **Purpose:** Heuristic shortest path
- **Heuristic:** Haversine distance to destination

### 3. Yen's K-Shortest Paths
- **Purpose:** Find K alternative routes
- **Complexity:** O(K × N × (E + V log V))

---

## 📚 Comparative Analysis

| Algorithm | Time Complexity | Space | Best For |
|-----------|----------------|-------|----------|
| Dijkstra  | O((V+E) log V) | O(V)  | Guaranteed shortest |
| A*        | Better in practice | O(V) | Faster with heuristic |
| Yen's     | O(K×N×(E+V log V)) | O(K×V) | Multiple alternatives |

---

## 📄 Project Deliverables

✅ **Technical**
- [x] Working code (Python/ML) on GitHub
- [x] Graph algorithms: Dijkstra, A*, Yen
- [x] ML models: XGBoost, RandomForest

✅ **Documentation**
- [x] Data preprocessing scripts
- [x] Comprehensive README
- [ ] IEEE format research paper (template provided)

✅ **Analysis**
- [x] Comparative analysis (3 algorithms)
- [x] Real-world validation (Hyderabad Metro)
- [x] Performance metrics (MAE, RMSE, R²)

---

## 🎯 Next Steps

1. Run data generation pipeline: `python scripts/run_all_pipelines.py`
2. Start backend: `python backend/main.py`
3. Start frontend: `npm run dev`
4. Test route optimization at `http://localhost:3000`
5. Review ML metrics at `http://localhost:8000/api/ml/metrics`
6. Generate visualizations for IEEE paper

---

**Project Status:** ✅ Phase 1 & 2 Complete
**Last Updated:** April 6, 2026
