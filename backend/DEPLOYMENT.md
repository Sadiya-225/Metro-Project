# Backend Deployment Guide (Render)

## Prerequisites
- Render account (free tier available at https://render.com)
- GitHub repository with your code pushed
- Frontend deployed on Vercel (to set CORS_ORIGINS)

---

## Step 1: Prepare Your Repository

Ensure these files are in your `backend/` directory:
- ✅ `render.yaml` - Render blueprint configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `main.py` - FastAPI application
- ✅ `.python-version` - Specifies Python 3.11.0

---

## Step 2: Deploy to Render

### Option A: Deploy via Blueprint (Recommended)

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Connect to Render**
   - Go to https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing your metro project
   - Render will automatically detect `backend/render.yaml`

3. **Configure Environment Variables** (if not in render.yaml)
   - `PORT`: 8000 (auto-set by Render)
   - `CORS_ORIGINS`: Your Vercel frontend URL (e.g., `https://metro-project-one.vercel.app`)
   - `PYTHON_VERSION`: 3.11.0
   - `PYTHONUNBUFFERED`: 1

4. **Deploy**
   - Click "Apply" to start deployment
   - Wait 3-5 minutes for build to complete

### Option B: Manual Web Service Deployment

1. Go to https://dashboard.render.com
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: metro-backend
   - **Region**: Oregon (US West)
   - **Branch**: main
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables (see above)
6. Click "Create Web Service"

---

## Step 3: Important Notes About Free Tier

### ⚠️ Limitations on Render Free Tier

1. **No Persistent Storage**
   - ML models and datasets will be rebuilt on each deployment
   - Models stored in `backend/models/` will NOT persist across restarts
   - Consider committing pre-trained models to Git (if < 100MB)

2. **Cold Starts**
   - Service spins down after 15 minutes of inactivity
   - First request after inactivity takes 30-60 seconds

3. **Resource Limits**
   - 512 MB RAM
   - Shared CPU
   - May struggle with large ML model training

### 📦 Handling Data & Models

**Option 1: Commit Models to Git** (Recommended if < 100MB total)
```bash
cd backend/models
git add *.pkl
git commit -m "Add pre-trained ML models"
git push
```

**Option 2: Generate on Startup** (Slower but works)
- Models will be trained during the startup event
- Adds ~30-60 seconds to cold start time
- Uses synthetic data from CSV files

**Option 3: Use External Storage** (Requires paid plan)
- Upgrade to Render Starter plan ($7/month)
- Add persistent disks for `/data` and `/models`
- Uncomment the `disks:` section in `render.yaml`

---

## Step 4: Verify Deployment

Once deployed, Render will provide a URL like: `https://metro-backend.onrender.com`

### Test Endpoints

1. **Health Check**
   ```bash
   curl https://metro-backend.onrender.com/
   ```
   Expected response:
   ```json
   {
     "status": "online",
     "service": "Metro Route Intelligence API",
     "version": "2.0.0"
   }
   ```

2. **API Documentation**
   - Visit: `https://metro-backend.onrender.com/docs`
   - Explore interactive Swagger UI

3. **Test Route Optimization**
   ```bash
   curl -X POST https://metro-backend.onrender.com/api/route/optimize \
     -H "Content-Type: application/json" \
     -d '{
       "source": "Ameerpet",
       "destination": "Nagole",
       "algorithm": "dijkstra",
       "k_paths": 3
     }'
   ```

---

## Step 5: Update Frontend to Use Deployed Backend

Update your frontend environment variables:

**Vercel Environment Variable:**
```
NEXT_PUBLIC_API_URL=https://metro-backend.onrender.com
```

Or update API calls in your Next.js code to use the deployed URL.

---

## Step 6: Update CORS Origins

After deploying backend, ensure `CORS_ORIGINS` environment variable includes your frontend URL:

```
CORS_ORIGINS=https://metro-project-one.vercel.app,http://localhost:3000
```

This allows both production and local development.

---

## Troubleshooting

### Build Fails
- **Check Python version**: Ensure `.python-version` has `3.11.0`
- **Check requirements.txt**: All dependencies listed with compatible versions
- **View logs**: Render dashboard → Service → Logs tab

### Service Crashes on Startup
- **Memory limit exceeded**: Reduce ML model size or upgrade plan
- **Missing data files**: Ensure CSV files are in Git or generated during startup
- **Import errors**: Check all dependencies in requirements.txt

### CORS Errors
- **Update CORS_ORIGINS**: Include exact frontend URL (no trailing slash)
- **Check protocol**: Must match (http vs https)
- **Restart service**: After updating environment variables

### Slow Performance
- **Cold starts**: First request after inactivity is slow
- **ML training**: Pre-commit trained models to avoid startup delays
- **Upgrade plan**: Consider Render Starter for better performance

---

## Monitoring

### View Logs
```bash
# From Render dashboard → Logs tab
# Or use Render CLI:
render logs -s metro-backend
```

### Health Monitoring
- Render automatically monitors `/` endpoint
- Service restarts if health check fails
- Configure in render.yaml: `healthCheckPath: /`

---

## Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `render.yaml` configured in backend directory
- [ ] `.python-version` file created (3.11.0)
- [ ] Pre-trained ML models committed (if using Option 1)
- [ ] Render service created and deployed
- [ ] CORS_ORIGINS updated with frontend URL
- [ ] API endpoints tested via `/docs`
- [ ] Frontend connected to deployed backend URL
- [ ] Cold start behavior tested
- [ ] Error monitoring set up

---

## Cost Optimization

### Stay on Free Tier
- Keep service small and efficient
- Commit pre-trained models to avoid retraining
- Accept cold start delays for low-traffic apps

### When to Upgrade ($7/month Starter)
- Need persistent storage for models/data
- Require faster response times (no cold starts)
- Higher traffic (> 100 requests/day)
- Need custom domain support

---

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Python on Render](https://render.com/docs/deploy-fastapi)
- [Render Blueprint Spec](https://render.com/docs/blueprint-spec)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)

---

**Deployment Status:** Ready for Render deployment
**Estimated Build Time:** 3-5 minutes
**Estimated Cold Start:** 30-60 seconds (free tier)
