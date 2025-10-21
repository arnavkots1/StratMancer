# Model Cleanup Guide

## Overview

The `cleanup_old_models.py` script helps manage disk space by removing old model versions while keeping the latest model and one backup for each ELO group.

## What It Does

For each ELO group (low, mid, high), the script:
- **Keeps:** Latest model + 1 backup (second-to-latest)
- **Deletes:** All older versions

Each "model version" includes 3 files:
1. Model file (`draft_<elo>_xgb_<timestamp>.pkl`)
2. Calibrator file (`calibrator_<elo>_<timestamp>.pkl`)
3. Model card (`modelcard_<elo>_<timestamp>.json`)

## Usage

### 1. Dry Run (Preview Only)

See what would be deleted without actually deleting anything:

```bash
python cleanup_old_models.py --dry-run
```

This will show:
- ✅ Which models will be kept (latest + backup)
- 🗑️ Which models will be deleted
- 📊 Summary statistics

### 2. Interactive Mode (with Confirmation)

Run the cleanup with a confirmation prompt:

```bash
python cleanup_old_models.py
```

You'll be asked to confirm before any files are deleted.

### 3. Auto-Confirm Mode (No Prompt)

Run the cleanup without confirmation (useful for scripts):

```bash
python cleanup_old_models.py --yes
```

⚠️ **Warning:** Files will be deleted immediately without confirmation!

### 4. Custom Models Directory

Specify a different models directory:

```bash
python cleanup_old_models.py --models-dir /path/to/models
```

## Example Output

```
======================================================================
Cleaning up LOW ELO models
======================================================================
Found 6 model versions for low ELO
📦 Keeping 2 versions:
  [LATEST] 20251021_153524 (3 files)
  [BACKUP] 20251021_001133 (3 files)
🗑️  Deleting 4 old versions:
  [OLD] 20251020_152541 (3 files)
    ❌ Deleted: draft_low_xgb_20251020_152541.pkl
    ❌ Deleted: calibrator_low_20251020_152541.pkl
    ❌ Deleted: modelcard_low_20251020_152541.json
  ...
```

## When to Run

- After training new models
- Before committing to version control
- When disk space is running low
- As part of CI/CD pipeline (with `--yes` flag)

## Safety Features

1. **Dry run mode:** Test before deleting
2. **Confirmation prompt:** Prevents accidental deletion
3. **Keeps backup:** Always keeps 2 versions per ELO
4. **Grouped deletion:** Ensures matching model/calibrator/card files are deleted together
5. **Error handling:** Reports any failures without stopping

## Recommended Workflow

```bash
# 1. Train new models
python -m ml_pipeline.models.train --model xgb --elo mid --features rich

# 2. Preview cleanup
python cleanup_old_models.py --dry-run

# 3. Run cleanup
python cleanup_old_models.py --yes

# 4. Verify (should see 18 files: 3 files × 2 versions × 3 ELOs)
dir ml_pipeline\models\trained\*.pkl | find /c ".pkl"  # Should show 12
dir ml_pipeline\models\modelcards\*.json | find /c ".json"  # Should show 6
```

## Disk Space Savings

Each model version set is approximately:
- **Model file:** 50-100 MB
- **Calibrator file:** 1-5 MB
- **Model card:** < 1 KB

With 6 old versions, you could save **300-600 MB** of disk space!

## Help

```bash
python cleanup_old_models.py --help
```

## Troubleshooting

### "No model files found for X ELO"
- Check that models exist in `ml_pipeline/models/trained/`
- Ensure you've trained models for that ELO

### "Permission denied" errors
- Close any programs using the model files
- Run with administrator privileges if needed

### Want to keep more backups?
- Edit the script and change `keep_timestamps = sorted_timestamps[:2]` to `[:3]` for 3 versions, etc.

## Notes

- The script is safe to run multiple times
- It only deletes files matching the pattern `draft_<elo>_*`, `calibrator_<elo>_*`, and `modelcard_<elo>_*`
- If a model version has mismatched files (e.g., model without calibrator), all matching files for that timestamp are still grouped together

