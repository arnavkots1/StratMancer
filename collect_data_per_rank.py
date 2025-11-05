"""
Enhanced data collection script with optimized rate limits per rank.
Uses looser but safe rate limits to maximize collection speed while avoiding rate limit errors.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.collectors.match_collector import MatchCollector
from src.utils.config_manager import get_config
from src.utils.rate_limiter import RateLimiter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_for_rank_optimized(
    rank: str,
    target_matches: int,
    api_key: str,
    region: str = 'na1',
    requests_per_second: int = 19,
    requests_per_2_minutes: int = 95
) -> Dict[str, any]:
    """
    Collect data for a specific rank with optimized rate limits.
    
    Args:
        rank: Rank tier to collect
        target_matches: Target number of matches
        api_key: Riot API key
        region: Region code
        requests_per_second: Rate limit per second (looser but safe)
        requests_per_2_minutes: Rate limit per 2 minutes (looser but safe)
        
    Returns:
        Dictionary with collection statistics
    """
    logger.info(f"=" * 70)
    logger.info(f"Starting optimized collection for {rank}")
    logger.info(f"Target matches: {target_matches}")
    logger.info(f"Rate limits: {requests_per_second}/sec, {requests_per_2_minutes}/2min")
    logger.info(f"=" * 70)
    
    start_time = datetime.now()
    
    # Create optimized rate limiter (looser but safe)
    rate_limiter = RateLimiter(
        requests_per_second=requests_per_second,
        requests_per_2_minutes=requests_per_2_minutes
    )
    
    # Initialize collector with custom rate limiter
    config = get_config()
    collector = MatchCollector(
        api_key=api_key,
        region=region,
        save_raw=config.should_save_raw()
    )
    
    # Override rate limiter with optimized one
    collector.rate_limiter = rate_limiter
    collector.api_client.rate_limiter = rate_limiter
    
    try:
        # Collect matches (returns total count, not list)
        total_collected = collector.collect_for_rank(rank, target_matches)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        stats = {
            'rank': rank,
            'target_matches': target_matches,
            'collected_matches': total_collected,
            'success_rate': total_collected / target_matches if target_matches > 0 else 0,
            'duration_seconds': duration,
            'duration_minutes': duration / 60,
            'matches_per_minute': total_collected / (duration / 60) if duration > 0 else 0,
            'requests_per_second': requests_per_second,
            'requests_per_2_minutes': requests_per_2_minutes,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
        }
        
        logger.info(f"Collection complete for {rank}")
        logger.info(f"  Collected: {stats['collected_matches']}/{stats['target_matches']} matches")
        logger.info(f"  Duration: {stats['duration_minutes']:.2f} minutes")
        logger.info(f"  Speed: {stats['matches_per_minute']:.2f} matches/minute")
        
        return stats
        
    except Exception as e:
        logger.error(f"Collection failed for {rank}: {e}", exc_info=True)
        raise


def collect_all_ranks_optimized(
    ranks: List[str],
    matches_per_rank: int,
    api_key: str,
    region: str = 'na1',
    requests_per_second: int = 19,
    requests_per_2_minutes: int = 95
) -> Dict[str, Dict]:
    """
    Collect data for all specified ranks with optimized rate limits.
    
    Args:
        ranks: List of ranks to collect
        matches_per_rank: Target matches per rank
        api_key: Riot API key
        region: Region code
        requests_per_second: Rate limit per second
        requests_per_2_minutes: Rate limit per 2 minutes
        
    Returns:
        Dictionary mapping rank to collection statistics
    """
    all_stats = {}
    total_start = datetime.now()
    
    logger.info(f"=" * 70)
    logger.info(f"OPTIMIZED DATA COLLECTION")
    logger.info(f"Ranks: {', '.join(ranks)}")
    logger.info(f"Matches per rank: {matches_per_rank}")
    logger.info(f"Rate limits: {requests_per_second}/sec, {requests_per_2_minutes}/2min")
    logger.info(f"=" * 70)
    
    for rank in ranks:
        try:
            stats = collect_for_rank_optimized(
                rank=rank,
                target_matches=matches_per_rank,
                api_key=api_key,
                region=region,
                requests_per_second=requests_per_second,
                requests_per_2_minutes=requests_per_2_minutes
            )
            all_stats[rank] = stats
            
        except Exception as e:
            logger.error(f"Failed to collect {rank}: {e}")
            all_stats[rank] = {
                'rank': rank,
                'error': str(e),
                'collected_matches': 0
            }
            continue
    
    total_end = datetime.now()
    total_duration = (total_end - total_start).total_seconds()
    total_matches = sum(s.get('collected_matches', 0) for s in all_stats.values())
    
    logger.info(f"=" * 70)
    logger.info(f"COLLECTION SUMMARY")
    logger.info(f"Total ranks: {len(ranks)}")
    logger.info(f"Total matches collected: {total_matches}")
    logger.info(f"Total duration: {total_duration / 60:.2f} minutes")
    logger.info(f"Average speed: {total_matches / (total_duration / 60):.2f} matches/minute")
    logger.info(f"=" * 70)
    
    for rank, stats in all_stats.items():
        if 'error' not in stats:
            logger.info(f"  {rank}: {stats['collected_matches']} matches in {stats['duration_minutes']:.2f} min")
        else:
            logger.warning(f"  {rank}: FAILED - {stats['error']}")
    
    return all_stats


def main():
    """Command-line interface for optimized data collection"""
    parser = argparse.ArgumentParser(
        description='Enhanced data collection with optimized rate limits per rank',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect 200 matches for GOLD and PLATINUM with optimized limits
  python collect_data_per_rank.py --ranks GOLD PLATINUM --matches-per-rank 200

  # Collect with custom rate limits (must be safe!)
  python collect_data_per_rank.py --ranks SILVER --matches-per-rank 150 --rps 18 --rpm 90

  # Collect all standard ranks (including EMERALD)
  python collect_data_per_rank.py --ranks IRON BRONZE SILVER GOLD PLATINUM EMERALD DIAMOND --matches-per-rank 200
        """
    )
    
    parser.add_argument(
        '--ranks',
        nargs='+',
        required=True,
        help='Ranks to collect (IRON, BRONZE, SILVER, GOLD, PLATINUM, EMERALD, DIAMOND, MASTER, GRANDMASTER, CHALLENGER)'
    )
    
    parser.add_argument(
        '--matches-per-rank',
        type=int,
        default=200,
        help='Target number of matches per rank (default: 200)'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        default='na1',
        help='Region code (na1, euw1, kr, etc.)'
    )
    
    parser.add_argument(
        '--rps',
        type=int,
        default=19,
        help='Requests per second (default: 19, safe but looser than original 20/sec, 100/2min)'
    )
    
    parser.add_argument(
        '--rpm',
        type=int,
        default=95,
        help='Requests per 2 minutes (default: 95, safe but looser than original 100/2min)'
    )
    
    args = parser.parse_args()
    
    # Validate rate limits are safe
    if args.rps > 20:
        logger.warning(f"WARNING: {args.rps} requests/sec exceeds typical development API limit (20/sec)")
        logger.warning("This may cause rate limit errors. Consider using production API key.")
    
    if args.rpm > 100:
        logger.warning(f"WARNING: {args.rpm} requests/2min exceeds typical development API limit (100/2min)")
        logger.warning("This may cause rate limit errors. Consider using production API key.")
    
    try:
        # Get configuration
        config = get_config()
        api_key = config.get_riot_api_key()
        
        # Collect matches
        stats = collect_all_ranks_optimized(
            ranks=args.ranks,
            matches_per_rank=args.matches_per_rank,
            api_key=api_key,
            region=args.region,
            requests_per_second=args.rps,
            requests_per_2_minutes=args.rpm
        )
        
        logger.info("Optimized collection completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

