# Railway Deployment Guide

## Quick Deploy to Railway

1. **Go to [Railway.app](https://railway.app)**
2. **Sign up with GitHub**
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your StratMancer repository**
6. **Railway will automatically detect it's a Python project**

## Environment Variables to Set

In Railway dashboard, go to your project → Variables tab and add:

```
PORT=8000
ENVIRONMENT=production
API_KEY=your-secret-api-key-here
```

## What Railway Will Do

- ✅ Automatically detect Python/FastAPI
- ✅ Install dependencies from `requirements.txt`
- ✅ Run `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
- ✅ Provide HTTPS URL
- ✅ Handle environment variables

## After Deployment

1. **Get your Railway URL** (e.g., `https://your-app.railway.app`)
2. **Update frontend** to use the new API URL
3. **Test the connection**

## Free Tier Limits

- **$5/month credit** (usually enough for small apps)
- **No credit card required**
- **Automatic HTTPS**
- **Custom domains available**

## Troubleshooting

- Check Railway logs if deployment fails
- Ensure all dependencies are in `requirements.txt`
- Verify environment variables are set correctly
