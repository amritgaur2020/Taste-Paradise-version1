# Render Deployment Guide for Taste Paradise

## Overview
This guide explains how to deploy both the frontend and backend of Taste Paradise on Render using Infrastructure as Code (render.yaml).

## Architecture
```
Render Platform
├── Frontend Service (React/Node.js) → taste-paradise-frontend.onrender.com
├── Backend Service (FastAPI/Python) → taste-paradise-backend.onrender.com
└── Integrated with MongoDB Atlas (Free Tier)
```

## Prerequisites
1. **Render Account** - Sign up at https://render.com (FREE)
2. **GitHub Repository** - Already configured ✓
3. **MongoDB Atlas Account** - https://www.mongodb.com/cloud/atlas (FREE)
4. **Environment Variables** - Configured in .env.example

## Step 1: Prepare MongoDB

### Create MongoDB Connection String
1. Go to MongoDB Atlas: https://cloud.mongodb.com
2. Create a free cluster
3. Get your connection string (format: mongodb+srv://username:password@cluster.mongodb.net/tasteparadise)
4. Keep this safe - you'll need it for deployment

## Step 2: Deploy on Render

### Automatic Deployment (Using Blueprint)
1. Go to https://render.com
2. Sign in with GitHub
3. Click **"New +"** → **"Blueprint"**
4. Select your `Taste-Paradise-version1` repository
5. Render will auto-detect `render.yaml` and show both services
6. Click **"Create New Service"**

### Set Environment Variables
Before deploying, configure these variables in Render:

**For Backend Service:**
- `MONGODB_URL` = Your MongoDB connection string
- `JWT_SECRET` = Generate a strong random string
- `PYTHONUNBUFFERED` = true (auto-set)

**For Frontend Service:**
- `REACT_APP_API_URL` = https://taste-paradise-backend.onrender.com (auto-set in render.yaml)
- `NODE_ENV` = production

### How to Add Environment Variables in Render:
1. Open the service settings
2. Go to "Environment" tab
3. Add each variable as Key-Value pair
4. Click "Save Changes"

## Step 3: Update Your Code

### Frontend Configuration
Make sure your frontend uses environment variables for the API URL.

**File: `frontend/src/config.js`**
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default {
  API_BASE_URL,
  // other config
};
```

**File: `frontend/src/App.js` or wherever you make API calls**
```javascript
import config from './config';

// Use in your API calls:
const response = await fetch(`${config.API_BASE_URL}/api/endpoint`);
```

### Backend CORS Configuration
Make sure your `main.py` has CORS enabled for your frontend domain.

**File: `main.py`**
```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://taste-paradise-frontend.onrender.com",
        "http://localhost:3000",  # for local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rest of your app...
```

## Step 4: Local Testing

Before deploying to Render, test locally:

### Terminal 1 - Backend
```bash
cd Taste-Paradise-version1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm start
```

Your app will be available at `http://localhost:3000`

## Step 5: Push to GitHub

After making all changes, commit and push:

```bash
git add .
git commit -m "Configure for Render deployment"
git push origin main
```

## Step 6: Monitor Deployment

After clicking "Create Service" on Render:

1. Render will pull from GitHub
2. Build logs will show in real-time
3. Frontend build: ~2-3 minutes
4. Backend build: ~3-5 minutes
5. Total: ~10-15 minutes for first deployment

**Check Status:**
- Go to https://dashboard.render.com
- Select your project
- Click each service to see build logs

## Troubleshooting

### Frontend Not Loading
**Problem:** "Cannot GET /" error
**Solution:** Check that `npm run build` completed successfully. Look in build logs.

### Backend 502 Error
**Problem:** Backend service not responding
**Solution:** 
- Check MongoDB connection string in environment variables
- Verify `MONGODB_URL` is correct
- Check build logs for Python errors

### CORS Errors
**Problem:** "Access-Control-Allow-Origin" errors in console
**Solution:** Update the `allow_origins` list in `main.py` with your Render domain

### Deployment Taking Too Long
**Problem:** Build stalled
**Solution:** 
- Check if requirements.txt has problematic packages
- Render has timeout limits - ensure your build completes within 30 minutes

## After Deployment

### Verify Everything Works
1. Visit `https://taste-paradise-frontend.onrender.com`
2. Your React app should load
3. Try making an API call to verify backend connection
4. Check browser console for errors (F12)

### Monitor Performance
- Render Dashboard shows service status
- Free tier services spin down after 15 minutes of inactivity
- They restart automatically when accessed

## Costs
- **Frontend (Node.js):** FREE (Render free tier)
- **Backend (Python):** FREE (Render free tier)
- **MongoDB:** FREE (Atlas free tier - 512MB storage)
- **Total Cost:** $0/month ✨

## What's Next

### Optimize for Production
1. Add error tracking (Sentry)
2. Set up monitoring and alerts
3. Enable HTTPS (auto-enabled on Render)
4. Configure custom domain

### Scale When Ready
- Upgrade to paid Render plans
- Use MongoDB paid tier for more storage
- Add Redis for caching
- Set up CI/CD pipelines

## Quick Reference

**Render Dashboard:** https://dashboard.render.com
**MongoDB Atlas:** https://cloud.mongodb.com
**Frontend URL:** https://taste-paradise-frontend.onrender.com
**Backend URL:** https://taste-paradise-backend.onrender.com
**Backend API Docs:** https://taste-paradise-backend.onrender.com/docs

## Support
- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- React Docs: https://react.dev

---

**Last Updated:** December 16, 2024
**Author:** Amrit Gaur
**Status:** ✓ Ready for Deployment
