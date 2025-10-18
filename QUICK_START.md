# Quick Start Guide - StratMancer

## Step-by-Step Instructions

### 1. Start the Backend API

**Open a terminal** (keep it running):

```bash
# Windows Command Prompt
python -m uvicorn backend.api.main:app --reload
```

Or **double-click**: `start_backend.bat`

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 2. Start the Frontend

**Open a second terminal**:

```bash
cd frontend
npm run dev
```

You should see:
```
▲ Next.js 14.2.33
- Local:        http://localhost:3000
✓ Ready in 2.4s
```

### 3. Open in Browser

Navigate to: **http://localhost:3000/draft**

---

## Troubleshooting

### "Champions not loading"

**Symptom**: Shows "No champions found" or loading forever

**Solution**: 
1. Check backend is running (see Step 1)
2. Verify: http://localhost:8000/healthz returns `{"status":"healthy"}`
3. Verify: http://localhost:8000/models/feature-map returns champion data

### "Port already in use"

**Backend (port 8000)**:
```bash
# Find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Frontend (port 3000)**:
```bash
# Use different port
cd frontend
set PORT=3001
npm run dev
```

### "Backend API connection refused"

Make sure the backend is running in a separate terminal:

```bash
# Check if it's running
curl http://localhost:8000/healthz
```

If not, start it:
```bash
python -m uvicorn backend.api.main:app --reload
```

---

## What You Should See

### Backend Terminal
```
INFO:     Will watch for changes in these directories: ['C:\\...\\StratMancer']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Frontend Terminal
```
  ▲ Next.js 14.2.33
  - Local:        http://localhost:3000
  - Environments: .env

 ✓ Starting...
 ✓ Ready in 2.4s
```

### Browser (http://localhost:3000/draft)
- Champion grid with 170+ champions
- Search and filter working
- Can select champions for Blue/Red teams
- "Predict Draft" button clickable

---

## Quick Test

Once both are running, test the connection:

1. **Backend Health**: http://localhost:8000/healthz
   - Should show: `{"status":"healthy","version":"1.0.0"}`

2. **Champion Data**: http://localhost:8000/models/feature-map
   - Should show JSON with champion data

3. **Frontend**: http://localhost:3000/draft
   - Should show champion grid with search

---

## Need Help?

- Backend logs show errors? Check `backend/api.log`
- Frontend not loading? Check browser console (F12)
- Still stuck? See full docs in `START_FRONTEND.md` and `STEP3D_SUMMARY.md`

