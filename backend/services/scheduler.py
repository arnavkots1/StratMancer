"""
Background job scheduler for StratMancer API.
Handles periodic maintenance tasks like index refreshing and patch detection.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[BackgroundScheduler] = None


class SchedulerService:
    """Manages background jobs for the StratMancer API"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_stats: Dict[str, Dict[str, Any]] = {}
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )
    
    def _job_executed_listener(self, event):
        """Log successful job execution"""
        job_id = event.job_id
        if job_id in self.job_stats:
            self.job_stats[job_id]['last_success'] = datetime.now().isoformat()
            self.job_stats[job_id]['success_count'] += 1
    
    def _job_error_listener(self, event):
        """Log job errors"""
        job_id = event.job_id
        if job_id in self.job_stats:
            self.job_stats[job_id]['last_error'] = datetime.now().isoformat()
            self.job_stats[job_id]['error_count'] += 1
        logger.error(f"Job {job_id} failed: {event.exception}")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Background scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Background scheduler shutdown complete")
    
    def add_job(self, func, trigger, job_id: str, name: str, **kwargs):
        """Add a job to the scheduler"""
        self.scheduler.add_job(
            func,
            trigger,
            id=job_id,
            name=name,
            replace_existing=True,
            **kwargs
        )
        
        # Initialize stats
        self.job_stats[job_id] = {
            'name': name,
            'success_count': 0,
            'error_count': 0,
            'last_success': None,
            'last_error': None
        }
        
        logger.info(f"Scheduled job: {name} (ID: {job_id})")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        job = self.scheduler.get_job(job_id)
        if not job:
            return None
        
        stats = self.job_stats.get(job_id, {})
        
        return {
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger),
            **stats
        }
    
    def get_all_jobs_status(self) -> Dict[str, Any]:
        """Get status of all jobs"""
        jobs = self.scheduler.get_jobs()
        return {
            'scheduler_running': self.scheduler.running,
            'total_jobs': len(jobs),
            'jobs': [self.get_job_status(job.id) for job in jobs]
        }
    
    def run_job_now(self, job_id: str) -> bool:
        """Manually trigger a job to run immediately"""
        job = self.scheduler.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False
        
        try:
            logger.info(f"Manually triggering job: {job_id}")
            job.func()
            return True
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}", exc_info=True)
            return False


# ============================================================================
# Job Functions
# ============================================================================

def refresh_history_index():
    """
    Job 1: Rebuild history index from latest processed matches.
    Runs hourly.
    """
    start_time = time.time()
    logger.info("🔄 Starting history index refresh...")
    
    try:
        from ml_pipeline.features.history_index import HistoryIndex
        
        # Paths
        data_dir = Path("data/processed")
        output_path = Path("ml_pipeline/history_index.json")
        
        # Check if data exists
        if not data_dir.exists():
            logger.warning(f"Data directory not found: {data_dir}")
            return
        
        # Find all match files
        match_files = list(data_dir.glob("matches_*.json"))
        
        if not match_files:
            logger.warning("No match files found in data/processed/")
            return
        
        logger.info(f"Found {len(match_files)} match file(s)")
        
        # Load all matches
        all_matches = []
        for match_file in match_files:
            try:
                with open(match_file, 'r') as f:
                    matches = json.load(f)
                    all_matches.extend(matches)
            except Exception as e:
                logger.error(f"Error loading {match_file}: {e}")
        
        if not all_matches:
            logger.warning("No matches loaded from files")
            return
        
        logger.info(f"Loaded {len(all_matches)} total matches")
        
        # Build history index
        history_index = HistoryIndex()
        history_index.build_from_matches(all_matches)
        
        # Save
        history_index.save(str(output_path))
        
        duration = time.time() - start_time
        logger.info(f"✅ History index refreshed successfully in {duration:.2f}s")
        logger.info(f"   Champion pairs: {len(history_index.synergy_matrix)}")
        logger.info(f"   Output: {output_path}")
    
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ History index refresh failed after {duration:.2f}s: {e}", exc_info=True)
        # Don't re-raise - we don't want to crash the scheduler


def refresh_model_registry():
    """
    Job 2: Re-read model cards to pick up newly trained models.
    Runs every 5 minutes.
    """
    start_time = time.time()
    logger.info("🔄 Starting model registry refresh...")
    
    try:
        from backend.services.model_registry import model_registry
        
        # Get old state
        old_models = model_registry.get_all_models()
        old_count = len(old_models)
        
        # Refresh registry
        model_registry.refresh()
        
        # Get new state
        new_models = model_registry.get_all_models()
        new_count = len(new_models)
        
        # Log changes
        if new_count > old_count:
            logger.info(f"✅ Model registry refreshed: {new_count} models (+{new_count - old_count} new)")
        elif new_count < old_count:
            logger.warning(f"⚠️ Model registry refreshed: {new_count} models ({old_count - new_count} removed)")
        else:
            logger.info(f"✅ Model registry refreshed: {new_count} models (no changes)")
        
        duration = time.time() - start_time
        logger.info(f"   Duration: {duration:.2f}s")
    
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Model registry refresh failed after {duration:.2f}s: {e}", exc_info=True)
        # Don't re-raise


def refresh_patch_meta():
    """
    Job 3: Query Riot API for current patch and store in config/meta.json.
    Runs daily.
    """
    start_time = time.time()
    logger.info("🔄 Starting patch metadata refresh...")
    
    try:
        from src.utils.riot_api_client import RiotAPIClient
        from backend.config import settings
        
        # Initialize API client
        api_client = RiotAPIClient(
            api_key=os.getenv("RIOT_API_KEY"),
            region="na1"
        )
        
        # Get current patch
        try:
            current_patch = api_client.get_current_patch()
            logger.info(f"Current patch from Riot API: {current_patch}")
        except Exception as e:
            logger.error(f"Failed to fetch patch from Riot API: {e}")
            # Use fallback
            current_patch = "15.20"
            logger.warning(f"Using fallback patch: {current_patch}")
        
        # Create config directory if needed
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Save metadata
        meta_path = config_dir / "meta.json"
        meta_data = {
            "patch": current_patch,
            "last_updated": datetime.now().isoformat(),
            "source": "riot_api" if current_patch != "15.20" else "fallback"
        }
        
        with open(meta_path, 'w') as f:
            json.dump(meta_data, f, indent=2)
        
        duration = time.time() - start_time
        logger.info(f"✅ Patch metadata refreshed successfully in {duration:.2f}s")
        logger.info(f"   Patch: {current_patch}")
        logger.info(f"   Output: {meta_path}")
    
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Patch metadata refresh failed after {duration:.2f}s: {e}", exc_info=True)
        # Don't re-raise


# ============================================================================
# Scheduler Initialization
# ============================================================================

def init_scheduler() -> SchedulerService:
    """Initialize and configure the background scheduler"""
    global scheduler
    
    logger.info("=" * 70)
    logger.info("Initializing Background Scheduler")
    logger.info("=" * 70)
    
    scheduler = SchedulerService()
    
    # Job 1: Refresh history index (hourly)
    scheduler.add_job(
        func=refresh_history_index,
        trigger=IntervalTrigger(hours=1),
        job_id='refresh_history_index',
        name='Refresh History Index',
        misfire_grace_time=300  # 5 minutes grace period
    )
    logger.info("  ✓ Scheduled: Refresh History Index (every 1 hour)")
    
    # Job 2: Refresh model registry (every 5 minutes)
    scheduler.add_job(
        func=refresh_model_registry,
        trigger=IntervalTrigger(minutes=5),
        job_id='refresh_model_registry',
        name='Refresh Model Registry',
        misfire_grace_time=60  # 1 minute grace period
    )
    logger.info("  ✓ Scheduled: Refresh Model Registry (every 5 minutes)")
    
    # Job 3: Refresh patch metadata (daily at 3 AM)
    scheduler.add_job(
        func=refresh_patch_meta,
        trigger=CronTrigger(hour=3, minute=0),
        job_id='refresh_patch_meta',
        name='Refresh Patch Metadata',
        misfire_grace_time=3600  # 1 hour grace period
    )
    logger.info("  ✓ Scheduled: Refresh Patch Metadata (daily at 3:00 AM)")
    
    logger.info("=" * 70)
    
    return scheduler


def get_scheduler() -> Optional[SchedulerService]:
    """Get the global scheduler instance"""
    return scheduler


# ============================================================================
# Helper Functions
# ============================================================================

def get_next_run_time(job_id: str) -> Optional[str]:
    """Get the next run time for a specific job"""
    if scheduler:
        status = scheduler.get_job_status(job_id)
        if status:
            return status.get('next_run')
    return None


def get_job_stats(job_id: str) -> Optional[Dict[str, Any]]:
    """Get statistics for a specific job"""
    if scheduler:
        return scheduler.get_job_status(job_id)
    return None


def trigger_job_manually(job_id: str) -> bool:
    """Manually trigger a job to run now"""
    if scheduler:
        return scheduler.run_job_now(job_id)
    return False

