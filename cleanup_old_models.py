#!/usr/bin/env python3
"""
Clean up old model files, keeping only the latest and one backup.

For each ELO group (low, mid, high), this script:
1. Finds all model files (.pkl) and model cards (.json)
2. Keeps the latest model + one backup (second-to-latest)
3. Deletes all older models to save disk space

Usage:
    python cleanup_old_models.py [--dry-run]
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def find_model_files(models_dir: Path, elo: str) -> Tuple[List[Path], List[Path], List[Path]]:
    """
    Find all model files for a given ELO.
    
    Returns:
        (model_files, calibrator_files, modelcard_files)
    """
    # Model files are in the 'trained/' subdirectory
    trained_dir = models_dir / "trained"
    modelcards_dir = models_dir / "modelcards"
    
    # Find all files for this ELO
    model_files = sorted(trained_dir.glob(f"draft_{elo}_*.pkl"))
    calibrator_files = sorted(trained_dir.glob(f"calibrator_{elo}_*.pkl"))
    modelcard_files = sorted(modelcards_dir.glob(f"modelcard_{elo}_*.json"))
    
    return model_files, calibrator_files, modelcard_files


def extract_timestamp(filepath: Path) -> str:
    """Extract timestamp from filename (format: *_YYYYMMDD_HHMMSS.ext)"""
    stem = filepath.stem
    parts = stem.split('_')
    
    # Find timestamp parts (date and time)
    for i, part in enumerate(parts):
        if len(part) == 8 and part.isdigit():  # Date: YYYYMMDD
            if i + 1 < len(parts) and len(parts[i + 1]) == 6 and parts[i + 1].isdigit():  # Time: HHMMSS
                return f"{part}_{parts[i + 1]}"
    
    return ""


def cleanup_elo_models(models_dir: Path, elo: str, dry_run: bool = False) -> Dict[str, int]:
    """
    Clean up models for a specific ELO, keeping latest + 1 backup.
    
    Returns:
        Statistics dict with counts of kept and deleted files
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Cleaning up {elo.upper()} ELO models")
    logger.info(f"{'='*70}")
    
    model_files, calibrator_files, modelcard_files = find_model_files(models_dir, elo)
    
    stats = {
        'kept': 0,
        'deleted': 0,
        'errors': 0
    }
    
    if not model_files:
        logger.warning(f"No model files found for {elo} ELO")
        return stats
    
    # Group files by timestamp
    files_by_timestamp: Dict[str, List[Path]] = {}
    
    for file in model_files + calibrator_files + modelcard_files:
        timestamp = extract_timestamp(file)
        if timestamp:
            if timestamp not in files_by_timestamp:
                files_by_timestamp[timestamp] = []
            files_by_timestamp[timestamp].append(file)
    
    # Sort timestamps (newest first)
    sorted_timestamps = sorted(files_by_timestamp.keys(), reverse=True)
    
    logger.info(f"Found {len(sorted_timestamps)} model versions for {elo} ELO")
    
    if len(sorted_timestamps) <= 2:
        logger.info(f"✅ Only {len(sorted_timestamps)} version(s) found, no cleanup needed")
        stats['kept'] = sum(len(files_by_timestamp[ts]) for ts in sorted_timestamps)
        return stats
    
    # Keep latest 2 versions (latest + 1 backup)
    keep_timestamps = sorted_timestamps[:2]
    delete_timestamps = sorted_timestamps[2:]
    
    logger.info(f"📦 Keeping {len(keep_timestamps)} versions:")
    for i, ts in enumerate(keep_timestamps):
        label = "LATEST" if i == 0 else "BACKUP"
        file_count = len(files_by_timestamp[ts])
        logger.info(f"  [{label}] {ts} ({file_count} files)")
        stats['kept'] += file_count
    
    logger.info(f"🗑️  Deleting {len(delete_timestamps)} old versions:")
    for ts in delete_timestamps:
        files = files_by_timestamp[ts]
        logger.info(f"  [OLD] {ts} ({len(files)} files)")
        
        for file in files:
            if dry_run:
                logger.info(f"    [DRY RUN] Would delete: {file.name}")
            else:
                try:
                    file.unlink()
                    logger.info(f"    ❌ Deleted: {file.name}")
                    stats['deleted'] += 1
                except Exception as e:
                    logger.error(f"    ⚠️  Error deleting {file.name}: {e}")
                    stats['errors'] += 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old model files, keeping only latest + 1 backup"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help="Skip confirmation prompt and delete files immediately"
    )
    parser.add_argument(
        '--models-dir',
        type=Path,
        default=Path('ml_pipeline/models'),
        help="Path to models directory (default: ml_pipeline/models)"
    )
    
    args = parser.parse_args()
    
    models_dir = args.models_dir
    if not models_dir.exists():
        logger.error(f"Models directory not found: {models_dir}")
        return 1
    
    logger.info(f"\n{'='*70}")
    logger.info("StratMancer Model Cleanup Tool")
    logger.info(f"{'='*70}")
    logger.info(f"Models directory: {models_dir.absolute()}")
    logger.info(f"Mode: {'DRY RUN (no files will be deleted)' if args.dry_run else 'LIVE (files will be deleted)'}")
    logger.info(f"{'='*70}")
    
    if args.dry_run:
        logger.warning("⚠️  DRY RUN MODE - No files will be deleted")
    else:
        logger.warning("⚠️  LIVE MODE - Files will be permanently deleted!")
        if not args.yes:
            response = input("\nContinue? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logger.info("Cancelled by user")
                return 0
        else:
            logger.warning("⚠️  Auto-confirmed with --yes flag")
    
    # Clean up each ELO
    total_stats = {
        'kept': 0,
        'deleted': 0,
        'errors': 0
    }
    
    for elo in ['low', 'mid', 'high']:
        stats = cleanup_elo_models(models_dir, elo, dry_run=args.dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("Summary")
    logger.info(f"{'='*70}")
    logger.info(f"✅ Files kept:    {total_stats['kept']}")
    logger.info(f"❌ Files deleted: {total_stats['deleted']}")
    if total_stats['errors'] > 0:
        logger.error(f"⚠️  Errors:        {total_stats['errors']}")
    logger.info(f"{'='*70}")
    
    if args.dry_run:
        logger.info("\n💡 Run without --dry-run to actually delete files")
    else:
        logger.info("\n✅ Cleanup complete!")
    
    return 0


if __name__ == '__main__':
    exit(main())

