# 🎯 StratMancer Smart Pick System

## ✅ Backend Implementation Complete

### New Endpoints

#### 1. **POST `/recommend/pick`** - Champion Pick Recommendations
Returns top N champion recommendations for a specific role based on current draft state.

**Request:**
```json
{
  "elo": "mid",
  "side": "blue",
  "role": "jungle",
  "blue": {
    "top": 266,
    "jungle": null,
    "mid": null,
    "adc": null,
    "support": null,
    "bans": [53, 89]
  },
  "red": {
    "top": 24,
    "jungle": null,
    "mid": null,
    "adc": null,
    "support": null,
    "bans": [421, 75]
  },
  "patch": "15.20",
  "top_n": 5
}
```

**Response:**
```json
{
  "side": "blue",
  "role": "jungle",
  "baseline_winrate": 0.52,
  "recommendations": [
    {
      "champion_id": 64,
      "champion_name": "Lee Sin",
      "win_gain": 0.042,
      "raw_win_gain": 0.039,
      "reasons": ["+Early power spike", "+High mobility", "+Strong engage"]
    },
    ...
  ],
  "model_version": "mid-xgb-recommender",
  "elo": "mid",
  "evaluated_champions": 95
}
```

#### 2. **POST `/recommend/ban`** - Champion Ban Recommendations
Suggests which champions to ban based on threat level.

**Request:**
```json
{
  "elo": "mid",
  "side": "blue",
  "blue": {"top": 266, ...},
  "red": {"top": 24, ...},
  "patch": "15.20",
  "top_n": 5
}
```

**Response:**
```json
{
  "side": "blue",
  "recommendations": [
    {
      "champion_id": 122,
      "champion_name": "Darius",
      "threat_level": 0.067,
      "reasons": ["Enemy Strong engage", "Enemy Early power spike", "Enemy Frontline presence"]
    },
    ...
  ],
  "model_version": "mid-xgb-recommender",
  "elo": "mid",
  "evaluated_champions": 80
}
```

### Key Features

✅ **ELO-Aware Recommendations**
- **Low ELO**: Penalizes mechanically complex champions (-0.3 skill cap weight)
- **Mid ELO**: Neutral (no skill cap adjustment)
- **High ELO**: Rewards high skill cap champions (+0.2 skill cap weight)

✅ **Smart Caching**
- LRU cache with 1000 entry limit
- Hash-based cache keys (elo + side + draft state)
- Instant responses for repeated queries

✅ **Intelligent Explanations**
- Analyzes champion tags (engage, CC, mobility, utility, sustain, poke)
- Considers damage types (AP/AD balance)
- Evaluates early vs late game power
- Provides 1-3 human-readable reasons per pick

✅ **Performance Optimized**
- Evaluates up to 100 champions for picks
- Evaluates up to 80 champions for bans
- Expected response time: <1s cold, <200ms cached

### How It Works

1. **Baseline**: Gets current draft win probability
2. **Simulation**: For each available champion:
   - Temporarily adds champion to team
   - Runs prediction model
   - Calculates win probability delta (Δ)
3. **ELO Adjustment**: Applies skill cap weighting based on rank
4. **Ranking**: Sorts by adjusted win gain (descending)
5. **Explanations**: Generates reasons based on champion tags
6. **Caching**: Stores result for instant future responses

---

## 🚨 **IMPORTANT: Fix NaN Predictions First!**

Before integrating the frontend UI, we need to fix the current prediction issue:

```
Blue Team: NaN%
Red Team: NaN%
Confidence: 100%
```

This suggests the model is returning invalid probabilities. Likely causes:
1. Feature assembly returning NaN values
2. Model predicting outside [0,1] range
3. Calibrator issue

**Next Step**: Debug the prediction pipeline to ensure valid probabilities before adding recommendation UI.

---

## 📋 Frontend Integration (TODO)

Once predictions are fixed:

### 1. Add "Suggest Pick" Buttons
- Place below each team's draft section
- Only show when there's an empty role to fill
- Disabled if no model available for ELO

### 2. Recommendation Card Component
```tsx
<RecommendationCard
  recommendations={[
    {
      champion_id: 64,
      champion_name: "Lee Sin",
      win_gain: 0.042,
      reasons: ["+Early power", "+High mobility"]
    }
  ]}
  onSelectChampion={(id) => handlePickChampion(id)}
/>
```

### 3. Visual Design
- Show top 5 picks as cards
- Green bar indicating win % gain
- Champion portrait
- Reason chips/badges
- Click to auto-select champion

---

## 🧪 Testing the API

### Test Pick Recommendations:
```bash
curl -X POST http://localhost:8000/recommend/pick \
  -H "Content-Type: application/json" \
  -H "X-STRATMANCER-KEY: dev-key-change-in-production" \
  -d '{
    "elo": "mid",
    "side": "blue",
    "role": "jungle",
    "blue": {"top": 266, "jungle": null, "mid": null, "adc": null, "support": null, "bans": [53]},
    "red": {"top": 24, "jungle": null, "mid": null, "adc": null, "support": null, "bans": [421]},
    "patch": "15.20",
    "top_n": 5
  }'
```

### Test Ban Recommendations:
```bash
curl -X POST http://localhost:8000/recommend/ban \
  -H "Content-Type: application/json" \
  -H "X-STRATMANCER-KEY: dev-key-change-in-production" \
  -d '{
    "elo": "mid",
    "side": "blue",
    "blue": {"top": null, "jungle": null, "mid": null, "adc": null, "support": null, "bans": []},
    "red": {"top": null, "jungle": null, "mid": null, "adc": null, "support": null, "bans": []},
    "patch": "15.20",
    "top_n": 5
  }'
```

---

## 📊 Expected Performance

- **Cold start**: ~500ms - 1s (first request, loads model)
- **Warm (uncached)**: ~200-400ms (model loaded, simulating 100 picks)
- **Cached**: <50ms (instant response)
- **Memory**: ~50MB additional (cached recommendations)

---

## 🔜 Next Steps

1. **Fix NaN predictions** ← PRIORITY
2. Test `/recommend/pick` and `/recommend/ban` endpoints
3. Create frontend recommendation UI components
4. Add "Suggest Pick" buttons to draft page
5. Display recommendations with visual win gain bars
6. Add loading states and error handling
7. Optional: Add "Auto-pick Best" button for quick drafting

