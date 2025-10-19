@echo off
echo ======================================================================
echo Retraining ALL ELO Models with Full Dataset
echo ======================================================================
echo.
echo This will train models for:
echo   - Low ELO (IRON, BRONZE, SILVER)
echo   - Mid ELO (GOLD, PLATINUM)  
echo   - High ELO (EMERALD, DIAMOND, MASTER, GRANDMASTER, CHALLENGER)
echo.
echo Using XGBoost with full dataset (~4000 matches)
echo ======================================================================
echo.

echo [1/3] Training LOW ELO model...
python ml_pipeline/models/train.py --model xgb --elo low
if errorlevel 1 (
    echo ERROR: Low ELO training failed!
    pause
    exit /b 1
)
echo.

echo [2/3] Training MID ELO model...
python ml_pipeline/models/train.py --model xgb --elo mid
if errorlevel 1 (
    echo ERROR: Mid ELO training failed!
    pause
    exit /b 1
)
echo.

echo [3/3] Training HIGH ELO model...
python ml_pipeline/models/train.py --model xgb --elo high
if errorlevel 1 (
    echo ERROR: High ELO training failed!
    pause
    exit /b 1
)
echo.

echo ======================================================================
echo ALL MODELS TRAINED SUCCESSFULLY!
echo ======================================================================
echo.
echo Next steps:
echo   1. Restart the backend API
echo   2. Test predictions with the new models
echo.
pause

