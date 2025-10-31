"""
Enhanced match data collector with optimized rate limits for accurate per-rank collection.
Uses slightly looser rate limits (18/sec, 90/2min) while remaining safe from rate limiting.
"""
import logging
import argparse
import time
from typing import List, Set, Dict, Optional
from pathlib import Path
from tqdm import tqdm

from ..utils.config_manager import get_config
from ..utils.riot_api_client import RiotAPIClient, RiotAPIError
from ..utils.rate_limiter import RateLimiter
from ..transformers.match_transformer import MatchTransformer
from ..storage.data_storage import DataStorage
from ..transformers.schema import MatchData
from .puuid_cache import PUUIDCache

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedMatchCollector:
    """
    Enhanced match collector with optimized rate limits and improved accuracy.
    Uses 18 requests/second and 90 requests per 2 minutes for safer but faster collection.
    """
    
    # Queue types
    QUEUE_RANKED_SOLO = 'RANKED_SOLO_5x5'
    
    # Divisions for standard tiers
    DIVISIONS = ['I', 'II', 'III', 'IV']
    
    # Standard tiers (not including Master+)
    STANDARD_TIERS = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND']
    
    def __init__(
        self, 
        api_key: str, 
        region: str = 'na1',
        save_raw: bool = False,
        requests_per_second: int = 18,
        requests_per_2_minutes: int = 90
    ):
        """
        Initialize enhanced match collector.
        
        Args:
            api_key: Riot API key
            region: Region code
            save_raw: Whether to save raw API responses
            requests_per_second: Rate limit per second (default: 18, looser but safe)
            requests_per_2_minutes: Rate limit per 2 minutes (default: 90, looser but safe)
        """
        self.config = get_config()
        
        # Use optimized rate limits (looser than standard 20/sec, 100/2min)
        self.rate_limiter = RateLimiter(
            requests_per_second=requests_per_second,
            requests_per_2_minutes=requests_per_2_minutes
        )
        
        self.api_client = RiotAPIClient(api_key, region, self.rate_limiter)
        self.transformer = MatchTransformer()
        self.storage = DataStorage(
            base_path=str(self.config.get_storage_path()),
            formats=self.config.get_storage_formats()
        )
        self.puuid_cache = PUUIDCache()
        
        self.save_raw = save_raw
        self.current_patch = self.api_client.get_current_patch()
        
        # Track processed matches to avoid duplicates
        self.processed_match_ids: Set[str] = set()
        
        cache_stats = self.puuid_cache.stats()
        logger.info(f"Enhanced match collector initialized for patch {self.current_patch}")
        logger.info(f"Rate limits: {requests_per_second}/sec, {requests_per_2_minutes}/2min")
        logger.info(f"PUUID cache loaded: {cache_stats['total_entries']} entries")
    
    def collect_for_rank(
        self, 
        rank: str, 
        target_matches: int = 100,
        min_matches_per_summoner: int = 5,
        max_matches_per_summoner: int = 20
    ) -> List[MatchData]:
        """
        Collect matches for a specific rank with improved accuracy.
        
        Args:
            rank: Rank tier (IRON, BRONZE, ..., CHALLENGER)
            target_matches: Target number of matches to collect
            min_matches_per_summoner: Minimum matches to try per summoner
            max_matches_per_summoner: Maximum matches to collect per summoner
            
        Returns:
            List of collected MatchData objects
        """
        rank = rank.upper()
        logger.info(f"Starting enhanced collection for {rank} (target: {target_matches} matches)")
        
        # Get summoners for this rank
        summoners = self._get_summoners_for_rank(rank, max_summoners=min(200, target_matches // 2))
        logger.info(f"Found {len(summoners)} summoners in {rank}")
        
        if not summoners:
            logger.warning(f"No summoners found for {rank}")
            return []
        
        # Collect matches with better distribution
        collected_matches = []
        summoners_attempted = 0
        consecutive_failures = 0
        max_consecutive_failures = 10
        
        with tqdm(total=target_matches, desc=f"Collecting {rank}") as pbar:
            for summoner in summoners:
                if len(collected_matches) >= target_matches:
                    break
                
                # Safety check for too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.warning(f"Too many consecutive failures ({consecutive_failures}). Trying next summoner batch...")
                    consecutive_failures = 0
                    continue
                
                try:
                    # Calculate how many matches we need from this summoner
                    remaining = target_matches - len(collected_matches)
                    matches_to_get = min(max_matches_per_summoner, max(min_matches_per_summoner, remaining))
                    
                    matches = self._collect_summoner_matches(
                        summoner['puuid'], 
                        rank,
                        limit=matches_to_get
                    )
                    
                    if matches:
                        collected_matches.extend(matches)
                        pbar.update(len(matches))
                        consecutive_failures = 0
                        summoners_attempted += 1
                        
                        # Save incrementally (every 50 matches)
                        if len(collected_matches) >= 50 and len(collected_matches) % 50 == 0:
                            self.storage.save_matches(collected_matches[-50:], rank)
                    else:
                        consecutive_failures += 1
                    
                    # Small delay between summoners to be respectful
                    time.sleep(0.05)
                    
                except RiotAPIError as e:
                    logger.warning(f"API error for summoner {summoner.get('summonerId')}: {e}")
                    consecutive_failures += 1
                    time.sleep(1)  # Wait a bit longer on API errors
                    continue
                except Exception as e:
                    logger.error(f"Failed to collect for summoner {summoner.get('summonerId')}: {e}")
                    consecutive_failures += 1
                    continue
        
        # Save remaining matches
        if collected_matches:
            self.storage.save_matches(collected_matches, rank)
        
        # Save PUUID cache
        self.puuid_cache.save()
        
        logger.info(f"Collection complete for {rank}: {len(collected_matches)} matches from {summoners_attempted} summoners")
        return collected_matches
    
    def collect_all_ranks(self, ranks: List[str] = None, matches_per_rank: int = 100):
        """
        Collect matches for all specified ranks with enhanced error handling.
        
        Args:
            ranks: List of ranks to collect (None = all ranks)
            matches_per_rank: Target matches per rank
        """
        if ranks is None:
            ranks = self.config.get_ranks()
        
        logger.info(f"Starting enhanced collection for ranks: {ranks}")
        logger.info(f"Target: {matches_per_rank} matches per rank")
        logger.info(f"Rate limits: {self.rate_limiter.requests_per_second}/sec, "
                   f"{self.rate_limiter.requests_per_2_minutes}/2min")
        
        results = {}
        for rank in ranks:
            try:
                start_time = time.time()
                matches = self.collect_for_rank(rank, matches_per_rank)
                elapsed = time.time() - start_time
                
                results[rank] = {
                    'count': len(matches),
                    'time_seconds': elapsed,
                    'success': True
                }
                
                logger.info(f"✓ {rank}: {len(matches)} matches in {elapsed:.1f}s")
                
                # Small delay between ranks
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"✗ Failed to collect for rank {rank}: {e}", exc_info=True)
                results[rank] = {
                    'count': 0,
                    'time_seconds': 0,
                    'success': False,
                    'error': str(e)
                }
                continue
        
        # Save PUUID cache
        self.puuid_cache.save()
        
        # Print summary statistics
        total_matches = sum(r['count'] for r in results.values())
        successful = sum(1 for r in results.values() if r['success'])
        
        logger.info("=" * 70)
        logger.info("Collection Summary")
        logger.info("=" * 70)
        logger.info(f"Total matches collected: {total_matches}")
        logger.info(f"Successful ranks: {successful}/{len(results)}")
        for rank, result in results.items():
            status = "✓" if result['success'] else "✗"
            logger.info(f"  {status} {rank}: {result['count']} matches")
        
        stats = self.storage.get_statistics()
        logger.info(f"\nStorage statistics: {stats}")
    
    def _get_summoners_for_rank(self, rank: str, max_summoners: int = 200) -> List[Dict]:
        """
        Get summoners for a specific rank with improved error handling.
        
        Args:
            rank: Rank tier
            max_summoners: Maximum summoners to retrieve
            
        Returns:
            List of summoner dictionaries with 'puuid' and 'summonerId'
        """
        summoners = []
        
        if rank in ['CHALLENGER', 'GRANDMASTER', 'MASTER']:
            # Get from apex leagues
            try:
                if rank == 'CHALLENGER':
                    league = self.api_client.get_challenger_league(self.QUEUE_RANKED_SOLO)
                elif rank == 'GRANDMASTER':
                    league = self.api_client.get_grandmaster_league(self.QUEUE_RANKED_SOLO)
                else:  # MASTER
                    league = self.api_client.get_master_league(self.QUEUE_RANKED_SOLO)
                
                if league and 'entries' in league:
                    entries = league['entries'][:max_summoners]
                    
                    total_entries = len(entries)
                    logger.info(f"Processing {total_entries} league entries for {rank}")
                    
                    for idx, entry in enumerate(entries, 1):
                        if len(summoners) >= max_summoners:
                            break
                        
                        # New API returns PUUID directly!
                        puuid = entry.get('puuid')
                        if puuid:
                            summoners.append({
                                'puuid': puuid,
                                'summonerId': entry.get('summonerId', puuid[:16])
                            })
                            
                            if len(summoners) % 50 == 0 or len(summoners) == max_summoners:
                                logger.info(f"Progress: {len(summoners)}/{max_summoners} summoners "
                                          f"({idx}/{total_entries} entries processed)")
                
            except Exception as e:
                logger.error(f"Failed to get {rank} league: {e}")
        
        else:
            # Get from standard tiers
            for division in self.DIVISIONS:
                if len(summoners) >= max_summoners:
                    break
                
                try:
                    page = 1
                    max_pages = 15  # Increased from 10 for better coverage
                    
                    while len(summoners) < max_summoners and page <= max_pages:
                        entries = self.api_client.get_league_entries(
                            self.QUEUE_RANKED_SOLO, rank, division, page
                        )
                        
                        if not entries:
                            break
                        
                        for entry in entries:
                            if len(summoners) >= max_summoners:
                                break
                            
                            # New API returns PUUID directly!
                            puuid = entry.get('puuid')
                            if puuid:
                                summoners.append({
                                    'puuid': puuid,
                                    'summonerId': entry.get('summonerId', puuid[:16])
                                })
                        
                        if len(summoners) % 50 == 0:
                            logger.info(f"Progress: {len(summoners)}/{max_summoners} summoners "
                                      f"(page {page}, {rank} {division})")
                        
                        page += 1
                        
                        # Small delay between pages
                        time.sleep(0.1)
                
                except Exception as e:
                    logger.error(f"Failed to get entries for {rank} {division}: {e}")
                    continue
        
        return summoners
    
    def _collect_summoner_matches(
        self, 
        puuid: str, 
        rank: str,
        limit: int = 20, 
        queue_id: int = 420
    ) -> List[MatchData]:
        """
        Collect and process matches for a summoner with improved error handling.
        
        Args:
            puuid: Player UUID
            rank: Rank tier for tagging
            limit: Maximum matches to collect
            queue_id: Queue ID (420 = Ranked Solo/Duo)
            
        Returns:
            List of processed MatchData objects
        """
        processed_matches = []
        
        try:
            # Get match IDs
            match_ids = self.api_client.get_match_ids_by_puuid(
                puuid, 
                start=0, 
                count=min(limit, 100),  # API max is 100
                queue=queue_id if queue_id else self.config.get_queue_id()
            )
            
            if not match_ids:
                return []
            
            for match_id in match_ids:
                # Skip if already processed
                if match_id in self.processed_match_ids:
                    continue
                
                # Limit to requested number
                if len(processed_matches) >= limit:
                    break
                
                try:
                    # Get match data
                    raw_match = self.api_client.get_match(match_id)
                    
                    if not raw_match:
                        continue
                    
                    # Save raw if configured
                    if self.save_raw:
                        self.storage.save_raw_match(match_id, raw_match)
                    
                    # Transform to schema
                    match_data = self.transformer.transform(raw_match, rank)
                    
                    if match_data:
                        # Filter by current patch (optional, but preferred)
                        if match_data.patch == self.current_patch or match_data.patch == "unknown":
                            processed_matches.append(match_data)
                            self.processed_match_ids.add(match_id)
                    
                except RiotAPIError as e:
                    logger.debug(f"Failed to get match {match_id}: {e}")
                    continue
                
                except Exception as e:
                    logger.error(f"Error processing match {match_id}: {e}")
                    continue
        
        except RiotAPIError as e:
            logger.warning(f"API error getting matches for PUUID {puuid[:8]}...: {e}")
        except Exception as e:
            logger.error(f"Failed to get matches for PUUID {puuid[:8]}...: {e}")
        
        return processed_matches


def main():
    """Command-line interface for enhanced match collector"""
    parser = argparse.ArgumentParser(
        description='Enhanced League of Legends match data collector with optimized rate limits'
    )
    
    parser.add_argument(
        '--ranks',
        nargs='+',
        help='Ranks to collect (IRON, BRONZE, SILVER, GOLD, PLATINUM, DIAMOND, MASTER, GRANDMASTER, CHALLENGER)',
        default=None
    )
    
    parser.add_argument(
        '--matches-per-rank',
        type=int,
        default=100,
        help='Target number of matches per rank'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        default='na1',
        help='Region code (na1, euw1, kr, etc.)'
    )
    
    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='Save raw API responses for debugging'
    )
    
    parser.add_argument(
        '--requests-per-second',
        type=int,
        default=18,
        help='Rate limit per second (default: 18, safe but faster than standard)'
    )
    
    parser.add_argument(
        '--requests-per-2min',
        type=int,
        default=90,
        help='Rate limit per 2 minutes (default: 90, safe but faster than standard)'
    )
    
    args = parser.parse_args()
    
    try:
        # Get configuration
        config = get_config()
        api_key = config.get_riot_api_key()
        
        # Initialize enhanced collector
        collector = EnhancedMatchCollector(
            api_key=api_key,
            region=args.region,
            save_raw=args.save_raw,
            requests_per_second=args.requests_per_second,
            requests_per_2_minutes=args.requests_per_2min
        )
        
        # Collect matches
        collector.collect_all_ranks(
            ranks=args.ranks,
            matches_per_rank=args.matches_per_rank
        )
        
        logger.info("Enhanced collection completed successfully")
        
    except Exception as e:
        logger.error(f"Enhanced collection failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

