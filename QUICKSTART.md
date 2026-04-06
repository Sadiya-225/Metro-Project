# 🚀 Quick Start Guide

Get your Metro Route Intelligence Dashboard running in **5 minutes**!

---

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python --version

# Check Node.js version (need 18+)
node --version
```

---

## Step 1: Generate Datasets (2-3 minutes)

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Go to scripts and generate all datasets
cd ../scripts
python run_all_pipelines.py
```

**Expected Output:**
```
🚇 HYDERABAD METRO - DATA ENGINEERING PIPELINE
===============================================
STEP 1/6: GTFS Ingestion
✅ Loaded 707 stops
✅ Loaded 3 routes
✅ Detected 2 interchange stations: ['AME', 'MGB']

STEP 2/6: Station Metadata Generation
✅ Generated metadata for 57 stations
   - Interchanges: 2
   - Terminals: 6
   - Smart City Priority: 12

STEP 3/6: Synthetic Delay Generation
⏱️  Generating 50,000 delay records...
✅ Generated 50000 delay records
   - Avg delay: 3.42 minutes

STEP 4/6: Peak Hour Labels
✅ Generated 721 hourly peak labels

STEP 5/6: Transfer Penalty Matrix
✅ Generated 156 transfer penalty records

STEP 6/6: OD Pair Benchmarks
✅ Generated 435 OD pair benchmarks

✅ ALL DATA PIPELINES COMPLETED SUCCESSFULLY
```

**Generated Files:**
- ✅ `data/station_metadata.csv`
- ✅ `data/synthetic_realtime_delays.csv` (50,000 records!)
- ✅ `data/peak_hour_labels.csv`
- ✅ `data/transfer_penalty_matrix.csv`
- ✅ `data/od_pair_benchmarks.csv`

---

## Step 2: Start Backend (30 seconds)

```bash
cd ../backend
python main.py
```

**Expected Output:**
```
🚀 Initializing Metro Route Intelligence Backend...
📂 Loading data...
✅ Loaded 57 stations
🔨 Building metro network graph...
✅ Graph built: 57 nodes, 79 edges
🔧 Engineering features...
✅ Features engineered: 15 features
📊 Train size: 40000, Test size: 10000
🤖 Training XGBoost model...
✅ XGBoost trained - MAE: 1.234, RMSE: 2.345, R2: 0.876
✅ Route engine initialized
✅ ML predictor initialized
✅ Backend ready!

INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test the API:**
Open http://localhost:8000/docs in your browser to see interactive API documentation!

---

## Step 3: Start Frontend (1 minute)

**Open a new terminal:**

```bash
# Install frontend dependencies (if not already done)
npm install --legacy-peer-deps

# Start development server
npm run dev
```

**Expected Output:**
```
▲ Next.js 16.2.2
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000

✓ Ready in 3.2s
```

---

## Step 4: Test the System

### Option A: API Testing

```bash
# Get all stations
curl http://localhost:8000/api/stations

# Optimize a route
curl -X POST http://localhost:8000/api/route/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "source": "Ameerpet",
    "destination": "Nagole",
    "algorithm": "dijkstra"
  }'

# Predict delay
curl -X POST http://localhost:8000/api/predict/delay \
  -H "Content-Type: application/json" \
  -d '{
    "station_id": "AME",
    "hour": 18,
    "is_peak": true,
    "weekday": true,
    "weather": "clear"
  }'

# Get bottlenecks
curl http://localhost:8000/api/bottlenecks?limit=10

# Get ML metrics
curl http://localhost:8000/api/ml/metrics
```

### Option B: Frontend Testing

1. Open http://localhost:3000
2. Select source and destination stations
3. Choose algorithm (Dijkstra/A*/Yen)
4. View route optimization results
5. See delay predictions and bottleneck analysis

---

## Verify Everything Works

### ✅ Backend Checklist

- [ ] Backend starts without errors
- [ ] `/api/stations` returns 57 stations
- [ ] `/api/route/optimize` calculates paths
- [ ] `/api/predict/delay` returns predictions
- [ ] `/api/ml/metrics` shows model performance

### ✅ Data Checklist

- [ ] `data/` folder contains 5 CSV files
- [ ] `station_metadata.csv` has 57 rows
- [ ] `synthetic_realtime_delays.csv` has 50,000 rows
- [ ] All CSVs open without errors

### ✅ Frontend Checklist

- [ ] Frontend opens at localhost:3000
- [ ] Can select stations
- [ ] Can view routes on map
- [ ] Charts and visualizations load

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError" when running Python scripts

**Solution:**
```bash
pip install -r backend/requirements.txt
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Issue: npm dependency conflicts

**Solution:**
```bash
npm install --legacy-peer-deps --force
```

### Issue: CSV files not generated

**Solution:**
```bash
# Make sure you're in the scripts directory
cd scripts
python run_all_pipelines.py
```

---

## Next Steps

1. **Explore the Dashboard**
   - Try different source-destination pairs
   - Compare Dijkstra vs A* vs Yen's algorithm
   - View delay predictions for peak vs off-peak hours

2. **Review Generated Data**
   - Open CSVs in Excel/LibreOffice
   - Analyze delay patterns
   - Study station importance scores

3. **Test ML Models**
   - Check model accuracy at `/api/ml/metrics`
   - Try different prediction scenarios
   - Review feature importance

4. **Write IEEE Paper**
   - Use `IEEE_PAPER_TEMPLATE.md` as starting point
   - Fill in actual metrics from your runs
   - Add screenshots from the dashboard

5. **Prepare for Submission**
   - Create PowerPoint presentation
   - Record demo video
   - Print report for hardcopy submission

---

## Project Structure Overview

```
metro-project/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── route_engine.py      # Dijkstra, A*, Yen
│   ├── ml_models.py         # XGBoost, RandomForest
│   └── requirements.txt
│
├── scripts/
│   ├── 01_gtfs_ingestion.py
│   ├── 02_station_metadata.py
│   ├── 03_synthetic_delays.py
│   ├── 04_peak_hour_labels.py
│   ├── 05_transfer_penalty.py
│   ├── 06_od_benchmarks.py
│   └── run_all_pipelines.py
│
├── data/                    # Generated by scripts
│   ├── station_metadata.csv
│   ├── synthetic_realtime_delays.csv
│   ├── peak_hour_labels.csv
│   ├── transfer_penalty_matrix.csv
│   └── od_pair_benchmarks.csv
│
├── app/                     # Next.js pages
├── components/              # React components
├── lib/                     # Utilities
├── public/                  # GTFS data
│
├── README.md                # Full documentation
├── QUICKSTART.md            # This file
└── IEEE_PAPER_TEMPLATE.md   # Paper template
```

---

## Getting Help

**Project Documentation:**
- Full README: [`README.md`](README.md)
- IEEE Paper Template: [`IEEE_PAPER_TEMPLATE.md`](IEEE_PAPER_TEMPLATE.md)
- API Docs: http://localhost:8000/docs (when backend is running)

**Troubleshooting:**
1. Check that Python 3.11+ is installed
2. Check that Node.js 18+ is installed
3. Verify all CSV files are generated in `data/` folder
4. Check backend logs for errors
5. Check frontend console for errors

---

## Success Criteria

You're ready to proceed when:
- ✅ All 5 CSV datasets generated
- ✅ Backend running on port 8000
- ✅ Frontend running on port 3000
- ✅ API endpoints responding correctly
- ✅ ML models loaded and predicting

---

**Estimated Total Setup Time:** 5 minutes
**Next Review Meeting:** Check project guidelines for schedule
**Submission Deadline:** 15th April 2026

Good luck! 🚀
