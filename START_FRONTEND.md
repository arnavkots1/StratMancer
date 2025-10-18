# Starting the StratMancer Frontend

## Quick Start

### 1. Install Node.js Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Copy example file
cp .env.example .env

# Edit with your settings (use notepad or any text editor)
notepad .env
```

Set these values:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=dev-test-key-12345
```

### 3. Start the Development Server

```bash
npm run dev
```

The frontend will start on **http://localhost:3000**

### 4. Open in Browser

Open your browser and navigate to:
- **Home Page**: http://localhost:3000
- **Draft Analyzer**: http://localhost:3000/draft

## What to Test

### Draft Analyzer Page

1. **Select Elo**: Choose low/mid/high from dropdown
2. **Add Champions**:
   - Use search box to find champions
   - Click role filter buttons (Top, Jungle, Mid, ADC, Support)
   - Click champion cards to select them
3. **Fill Teams**:
   - Select 5 champions for Blue Team
   - Select 5 champions for Red Team
   - Optionally add bans (up to 5 per team)
4. **Get Prediction**:
   - Click "Predict Draft" button
   - View win probability and insights

## Expected Behavior

### Success Flow
1. Champion grid loads with all champions
2. Search/filter updates grid in real-time
3. Selected champions appear in role slots
4. Predict button triggers API call
5. Prediction card displays with:
   - Win probability (Blue vs Red)
   - Confidence score
   - Key factors with impact scores

### Error Handling
- If backend is down: "Failed to load champion data"
- If prediction fails: Error message with details
- If no champions selected: "Please select champions for both teams"

## Checking If It Works

### 1. Frontend Loads
✅ Page displays without errors  
✅ Header shows "StratMancer"  
✅ Champion grid is visible  

### 2. Search & Filters Work
✅ Typing in search box filters champions  
✅ Role buttons filter by position  
✅ Tag chips filter by style  

### 3. Draft Building Works
✅ Clicking champion adds to team  
✅ Role slots fill with champions  
✅ Remove button clears slot  
✅ Team stats update (Engage, CC, Sustain)  

### 4. Predictions Work
✅ Predict button triggers API call  
✅ Loading spinner shows during call  
✅ Prediction card displays results  
✅ Win probability bar animates  
✅ Key factors display with icons  

## Troubleshooting

### "Cannot connect to API"

**Problem**: Frontend can't reach backend

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/healthz

# Should return: {"status":"healthy","version":"1.0.0"}
```

If backend is not running:
```bash
cd backend
uvicorn backend.api.main:app --reload
```

### "Failed to load champion data"

**Problem**: Backend `/models/feature-map` endpoint not found

**Solution**:
1. Ensure feature_map.json exists:
   ```bash
   ls ml_pipeline/feature_map.json
   ```

2. If missing, generate it:
   ```bash
   python ml_pipeline/features/tag_builder.py --data_dir ./data --out ./ml_pipeline/feature_map.json --overrides ./ml_pipeline/tags_overrides.yaml
   ```

### Port 3000 Already in Use

**Problem**: Another app is using port 3000

**Solution**:
```bash
# Use different port
PORT=3001 npm run dev
```

Then access at http://localhost:3001

### Build Errors

**Problem**: TypeScript or dependency errors

**Solution**:
```bash
# Clear cache
rm -rf .next node_modules

# Reinstall
npm install

# Retry
npm run dev
```

## Development Tips

### Hot Reload
- Changes to files auto-reload the page
- No need to restart server

### Console Logs
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for API calls

### API Calls
- All API calls logged to console
- Check Network tab for request/response details

## Production Build

To build for production:

```bash
npm run build
npm start
```

Production server runs on port 3000 by default.

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_API_KEY` | API authentication | `dev-test-key-12345` |

> **Note**: Must start with `NEXT_PUBLIC_` to be available in browser

## Next Steps

Once frontend is working:

1. ✅ Test draft predictions
2. ✅ Try different champion combinations
3. ✅ Experiment with elo settings
4. 🎮 Share with friends for feedback!

---

**Need help?** Check the [README.md](frontend/README.md) for detailed documentation.

