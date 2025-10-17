"""
Main match data collector for League of Legends matches.
Fetches matches across all ranks with automatic patch tagging and elo filtering.
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MatchCollector:
    """Collects and processes League of Legends match data"""
    
    # Queue types
    QUEUE_RANKED_SOLO = 'RANKED_SOLO_5x5'
    
    # Divisions for standard tiers
    DIVISIONS = ['I', 'II', 'III', 'IV']
    
    # Standard tiers (not including Master+)
    STANDARD_TIERS = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND']
    
    def __init__(self, api_key: str, region: str = 'na1', 
                 save_raw: bool = False):
        """
        Initialize match collector.
        
        Args:
            api_key: Riot API key
            region: Region code
            save_raw: Whether to save raw API responses
        """
        self.config = get_config()
        self.rate_limiter = RateLimiter(
            requests_per_second=self.config.get('riot_api.rate_limits.requests_per_second', 20),
            requests_per_2_minutes=self.config.get('riot_api.rate_limits.requests_per_2_minutes', 100)
        )
        
        self.api_client = RiotAPIClient(api_key, region, self.rate_limiter)
        self.transformer = MatchTransformer()
        self.storage = DataStorage(
            base_path=str(self.config.get_storage_path()),
            formats=self.config.get_storage_formats()
        )
        
        self.save_raw = save_raw
        self.current_patch = self.api_client.get_current_patch()
        
        # Track processed matches to avoid duplicates
        self.processed_match_ids: Set[str] = set()
        
        logger.info(f"Match collector initialized for patch {self.current_patch}")
    
    def collect_for_rank(self, rank: str, target_matches: int = 100) -> List[MatchData]:
        """
        Collect matches for a specific rank.
        
        Args:
            rank: Rank tier (IRON, BRONZE, ..., CHALLENGER)
            target_matches: Target number of matches to collect
            
        Returns:
            List of collected MatchData objects
        """
        rank = rank.upper()
        logger.info(f"Starting collection for {rank} (target: {target_matches} matches)")
        
        # Get summoners for this rank
        summoners = self._get_summoners_for_rank(rank)
        logger.info(f"Found {len(summoners)} summoners in {rank}")
        
        if not summoners:
            logger.warning(f"No summoners found for {rank}")
            return []
        
        # Collect matches
        collected_matches = []
        
        with tqdm(total=target_matches, desc=f"Collecting {rank}") as pbar:
            for summoner in summoners:
                if len(collected_matches) >= target_matches:
                    break
                
                try:
                    matches = self._collect_summoner_matches(
                        summoner['puuid'], 
                        rank,
                        limit=min(20, target_matches - len(collected_matches))
                    )
                    
                    collected_matches.extend(matches)
                    pbar.update(len(matches))
                    
                    # Save incrementally
                    if len(collected_matches) >= 50:
                        self.storage.save_matches(collected_matches, rank)
                        collected_matches = []
                    
                except Exception as e:
                    logger.error(f"Failed to collect for summoner {summoner.get('summonerId')}: {e}")
                    continue
        
        # Save remaining matches
        if collected_matches:
            self.storage.save_matches(collected_matches, rank)
        
        logger.info(f"Collection complete for {rank}")
        return collected_matches
    
    def collect_all_ranks(self, ranks: List[str] = None, matches_per_rank: int = 100):
        """
        Collect matches for all specified ranks.
        
        Args:
            ranks: List of ranks to collect (None = all ranks)
            matches_per_rank: Target matches per rank
        """
        if ranks is None:
            ranks = self.config.get_ranks()
        
        logger.info(f"Collecting matches for ranks: {ranks}")
        logger.info(f"Target: {matches_per_rank} matches per rank")
        
        for rank in ranks:
            try:
                self.collect_for_rank(rank, matches_per_rank)
            except Exception as e:
                logger.error(f"Failed to collect for rank {rank}: {e}", exc_info=True)
                continue
        
        # Print statistics
        stats = self.storage.get_statistics()
        logger.info(f"Collection complete. Total matches: {stats['total_matches']}")
        logger.info(f"Matches by rank: {stats['by_rank']}")
    
    def _get_summoners_for_rank(self, rank: str, max_summoners: int = 100) -> List[Dict]:
        """
        Get summoners for a specific rank.
        
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
                    
                    for entry in entries:
                        summoner_id = entry.get('summonerId')
                        if summoner_id:
                            try:
                                # Get summoner to obtain PUUID
                                summoner = self.api_client._request(
                                    f"{self.api_client.base_url}/lol/summoner/v4/summoners/{summoner_id}"
                                )
                                if summoner:
                                    summoners.append({
                                        'puuid': summoner['puuid'],
                                        'summonerId': summoner_id
                                    })
                            except Exception as e:
                                logger.debug(f"Failed to get summoner {summoner_id}: {e}")
                                continue
                
            except Exception as e:
                logger.error(f"Failed to get {rank} league: {e}")
        
        else:
            # Get from standard tiers
            for division in self.DIVISIONS:
                if len(summoners) >= max_summoners:
                    break
                
                try:
                    page = 1
                    while len(summoners) < max_summoners:
                        entries = self.api_client.get_league_entries(
                            self.QUEUE_RANKED_SOLO, rank, division, page
                        )
                        
                        if not entries:
                            break
                        
                        for entry in entries:
                            if len(summoners) >= max_summoners:
                                break
                            
                            summoner_id = entry.get('summonerId')
                            if summoner_id:
                                try:
                                    summoner = self.api_client._request(
                                        f"{self.api_client.base_url}/lol/summoner/v4/summoners/{summoner_id}"
                                    )
                                    if summoner:
                                        summoners.append({
                                            'puuid': summoner['puuid'],
                                            'summonerId': summoner_id
                                        })
                                except Exception as e:
                                    logger.debug(f"Failed to get summoner {summoner_id}: {e}")
                                    continue
                        
                        page += 1
                        
                        # Limit pages to avoid excessive requests
                        if page > 5:
                            break
                
                except Exception as e:
                    logger.error(f"Failed to get entries for {rank} {division}: {e}")
                    continue
        
        return summoners
    
    def _collect_summoner_matches(self, puuid: str, rank: str, 
                                  limit: int = 20) -> List[MatchData]:
        """
        Collect and process matches for a summoner.
        
        Args:
            puuid: Player UUID
            rank: Rank tier for tagging
            limit: Maximum matches to collect
            
        Returns:
            List of processed MatchData objects
        """
        processed_matches = []
        
        try:
            # Get match IDs
            match_ids = self.api_client.get_match_ids_by_puuid(
                puuid, 
                start=0, 
                count=limit,
                queue=self.config.get_queue_id()
            )
            
            for match_id in match_ids:
                # Skip if already processed
                if match_id in self.processed_match_ids:
                    continue
                
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
                        # Filter by current patch (optional)
                        if match_data.patch == self.current_patch or match_data.patch == "unknown":
                            processed_matches.append(match_data)
                            self.processed_match_ids.add(match_id)
                    
                except RiotAPIError as e:
                    logger.debug(f"Failed to get match {match_id}: {e}")
                    continue
                
                except Exception as e:
                    logger.error(f"Error processing match {match_id}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to get matches for PUUID {puuid}: {e}")
        
        return processed_matches


def main():
    """Command-line interface for match collector"""
    parser = argparse.ArgumentParser(description='Collect League of Legends match data')
    
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
    
    args = parser.parse_args()
    
    try:
        # Get configuration
        config = get_config()
        api_key = config.get_riot_api_key()
        
        # Initialize collector
        collector = MatchCollector(
            api_key=api_key,
            region=args.region,
            save_raw=args.save_raw
        )
        
        # Collect matches
        collector.collect_all_ranks(
            ranks=args.ranks,
            matches_per_rank=args.matches_per_rank
        )
        
        logger.info("Collection completed successfully")
        
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

