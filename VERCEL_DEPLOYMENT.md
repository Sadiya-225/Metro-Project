# Vercel Deployment Guide

## Overview

This Metro Route Intelligence Dashboard can be deployed to Vercel for the frontend, but requires a separate backend deployment for Python APIs.

---

## Architecture for Deployment

```
┌─────────────────────┐
│   Vercel (Frontend) │
│   Next.js App       │
│   Port 3000         │
└──────────┬──────────┘
           │
           │ API Calls
           │
           ▼
┌─────────────────────┐
│  Backend (Python)   │
│  FastAPI Server     │
│  Port 8000          │
└─────────────────────┘
```

---

## Option 1: Split Deployment (Recommended)

### Frontend on Vercel

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/metro-project.git
   git push -u origin main
   ```

2. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Configure:
     - Framework Preset: Next.js
     - Root Directory: `./` (default)
     - Build Command: `npm run build`
     - Output Directory: `.next`

3. **Environment Variables**
   Add in Vercel dashboard:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```

### Backend on Render/Railway/Fly.io

**Option A: Render.com**
1. Create new "Web Service"
2. Connect GitHub repo
3. Configure:
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && python main.py`
   - Environment: Python 3.11

**Option B: Railway.app**
1. Create new project from GitHub
2. Add Python service
3. Configure:
   - Root Directory: `backend`
   - Start Command: `python main.py`

**Option C: Fly.io**
Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

Deploy:
```bash
cd backend
fly launch
fly deploy
```

---

## Option 2: All-in-One (Vercel + Serverless Functions)

**Note:** This requires converting Python backend to TypeScript/JavaScript serverless functions.

Create `api/` folder with serverless functions:
```typescript
// api/stations.ts
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
) {
  // Call Python backend or implement logic here
  res.json({ stations: [] });
}
```

**Limitations:**
- Python ML models need to be ported or called via external service
- 10-second timeout on serverless functions
- Cold starts may affect performance

---

## Option 3: Pre-Generated Data (Static)

For demo/presentation purposes:

1. **Generate all data locally:**
   ```bash
   cd scripts
   python run_all_pipelines.py
   ```

2. **Commit data files:**
   ```bash
   git add data/*.csv
   git commit -m "Add pre-generated data"
   git push
   ```

3. **Modify frontend to use static data:**
   - Place CSVs in `public/data/`
   - Use Papa Parse or similar to read CSVs client-side
   - Remove API calls to backend

4. **Deploy frontend only to Vercel**

---

## Data Generation for Production

### Manual Setup (One-Time)

Before deploying, generate all datasets:

```bash
cd scripts
python run_all_pipelines.py
```

This creates:
- `data/station_metadata.csv` (57 stations)
- `data/synthetic_realtime_delays.csv` (50,000 records)
- `data/peak_hour_labels.csv` (721 records)
- `data/transfer_penalty_matrix.csv` (156 records)
- `data/od_pair_benchmarks.csv` (435 pairs)

### Using Data Setup Dashboard

The `/data-setup` page provides a UI for:
- Uploading GTFS and OSM files
- Running data generation pipeline
- Monitoring step-by-step progress

**Requirements:**
- Backend must be running
- Backend needs write access to `data/` folder
- Each step takes 10-60 seconds

---

## Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Local development
# OR
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com  # Production
```

### Backend (.env)
```bash
PORT=8000
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app
DATA_DIR=../data
```

---

## File Structure for Deployment

```
metro-project/
├── .vercelignore          # Exclude backend from Vercel
├── vercel.json            # Vercel configuration
├── backend/
│   ├── Dockerfile         # For backend deployment
│   ├── requirements.txt
│   └── main.py
├── data/                  # Pre-generated datasets
│   ├── station_metadata.csv
│   └── synthetic_realtime_delays.csv
└── app/                   # Next.js frontend
```

### .vercelignore
```
backend/
scripts/
data/
*.py
*.pkl
models/
```

### vercel.json
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["iad1"]
}
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Generate all datasets (`python scripts/run_all_pipelines.py`)
- [ ] Test frontend locally (`npm run dev`)
- [ ] Test backend locally (`python backend/main.py`)
- [ ] Verify API calls work between frontend and backend
- [ ] Update CORS origins in `backend/main.py`

### Frontend Deployment (Vercel)
- [ ] Push code to GitHub
- [ ] Connect repository to Vercel
- [ ] Set `NEXT_PUBLIC_API_URL` environment variable
- [ ] Deploy
- [ ] Test deployed site

### Backend Deployment (Render/Railway/Fly.io)
- [ ] Choose hosting platform
- [ ] Create new service
- [ ] Set environment variables
- [ ] Deploy
- [ ] Test API endpoints
- [ ] Update frontend `NEXT_PUBLIC_API_URL`

### Post-Deployment
- [ ] Test all three algorithms (Dijkstra, A*, Yen)
- [ ] Test ML prediction page
- [ ] Test bottlenecks page
- [ ] Verify map displays correctly
- [ ] Check API response times

---

## Troubleshooting

### CORS Errors
Update `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app",  # Add your Vercel URL
        "https://*.vercel.app"  # Wildcard for preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Timeout
Increase timeout in frontend:
```typescript
const response = await fetch(url, {
  signal: AbortSignal.timeout(30000)  // 30 seconds
});
```

### Large File Uploads
For GTFS uploads, increase backend limits:
```python
from fastapi import UploadFile, File

@app.post("/api/upload/gtfs")
async def upload_gtfs(files: List[UploadFile] = File(...)):
    # Handle uploads
    pass
```

---

## Cost Estimates

### Vercel (Frontend)
- **Hobby Plan**: FREE
  - 100 GB bandwidth
  - Unlimited requests
  - Perfect for this project

### Backend Hosting

**Render.com**
- **Free Tier**: $0/month
  - 750 hours/month
  - Spins down after inactivity

**Railway.app**
- **Starter**: $5/month
  - $5 credit included
  - Pay only for usage

**Fly.io**
- **Free Tier**: $0/month
  - 3 shared-cpu VMs
  - 160 GB bandwidth

---

## Recommended Setup for Demo/Presentation

1. **Deploy frontend to Vercel** (takes 5 minutes)
2. **Deploy backend to Render** (takes 10 minutes)
3. **Use pre-generated data** (no dynamic generation needed)
4. **Total cost: $0** (using free tiers)

---

## For Production Use

1. **Frontend**: Vercel Pro ($20/month)
2. **Backend**: Render Standard ($7/month) or Railway Pro ($20/month)
3. **Database**: PostgreSQL on Supabase (free tier)
4. **Monitoring**: Sentry (free tier)

---

**Last Updated:** April 6, 2026
**Author:** Ms. Sadiya Maheen Siddiqui
