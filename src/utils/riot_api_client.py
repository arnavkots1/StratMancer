"""
Riot API client with rate limiting and error handling.
"""
import logging
import requests
from typing import Dict, List, Optional, Any
from .rate_limiter import RateLimiter, retry_on_rate_limit

logger = logging.getLogger(__name__)


class RiotAPIError(Exception):
    """Base exception for Riot API errors"""
    pass


class RiotAPIClient:
    """
    Client for interacting with Riot Games API.
    Handles authentication, rate limiting, and error handling.
    """
    
    # API endpoints
    BASE_URLS = {
        'na1': 'https://na1.api.riotgames.com',
        'euw1': 'https://euw1.api.riotgames.com',
        'eun1': 'https://eun1.api.riotgames.com',
        'kr': 'https://kr.api.riotgames.com',
        'br1': 'https://br1.api.riotgames.com',
        'la1': 'https://la1.api.riotgames.com',
        'la2': 'https://la2.api.riotgames.com',
        'oc1': 'https://oc1.api.riotgames.com',
        'tr1': 'https://tr1.api.riotgames.com',
        'ru': 'https://ru.api.riotgames.com',
        'jp1': 'https://jp1.api.riotgames.com',
        'americas': 'https://americas.api.riotgames.com',
        'europe': 'https://europe.api.riotgames.com',
        'asia': 'https://asia.api.riotgames.com',
    }
    
    # Regional routing
    REGIONAL_ROUTING = {
        'na1': 'americas',
        'br1': 'americas',
        'la1': 'americas',
        'la2': 'americas',
        'euw1': 'europe',
        'eun1': 'europe',
        'tr1': 'europe',
        'ru': 'europe',
        'kr': 'asia',
        'jp1': 'asia',
        'oc1': 'asia',
    }
    
    def __init__(self, api_key: str, region: str = 'na1', 
                 rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize Riot API client.
        
        Args:
            api_key: Riot API key
            region: Region code (na1, euw1, kr, etc.)
            rate_limiter: Optional rate limiter instance
        """
        self.api_key = api_key
        self.region = region.lower()
        self.rate_limiter = rate_limiter or RateLimiter()
        
        if self.region not in self.BASE_URLS:
            raise ValueError(f"Invalid region: {region}")
        
        self.base_url = self.BASE_URLS[self.region]
        self.regional_url = self.BASE_URLS[self.REGIONAL_ROUTING.get(self.region, 'americas')]
        
        # Session for connection pooling with retry adapter
        self.session = requests.Session()
        self.session.headers.update({
            'X-Riot-Token': self.api_key,
            'Accept': 'application/json'
        })
        
        # Configure retry strategy for connection issues
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        logger.info(f"Riot API client initialized for region: {region}")
    
    @retry_on_rate_limit
    def _request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a rate-limited request to the API.
        
        Args:
            url: Full URL to request
            params: Query parameters
            
        Returns:
            JSON response
            
        Raises:
            RiotAPIError: On API errors
        """
        self.rate_limiter.acquire()
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            # Log rate limit status
            if response.status_code == 429:
                logger.error("Rate limit exceeded despite rate limiter")
                raise RiotAPIError("Rate limit exceeded")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.debug(f"Resource not found: {url}")
                return None
            elif e.response.status_code == 403:
                raise RiotAPIError("API key invalid or expired")
            elif e.response.status_code >= 500:
                logger.warning(f"Server error: {e.response.status_code}")
                raise RiotAPIError(f"Riot API server error: {e.response.status_code}")
            else:
                raise RiotAPIError(f"API request failed: {e}")
        
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout: {url}")
            raise RiotAPIError("Request timeout")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            raise RiotAPIError(f"Request failed: {e}")
    
    def get_summoner_by_name(self, summoner_name: str) -> Optional[Dict]:
        """Get summoner by name"""
        url = f"{self.base_url}/lol/summoner/v4/summoners/by-name/{summoner_name}"
        return self._request(url)
    
    def get_summoner_by_puuid(self, puuid: str) -> Optional[Dict]:
        """Get summoner by PUUID"""
        url = f"{self.base_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return self._request(url)
    
    def get_league_entries(self, queue: str, tier: str, division: str, 
                          page: int = 1) -> List[Dict]:
        """
        Get league entries for a specific tier and division.
        
        Args:
            queue: Queue type (RANKED_SOLO_5x5, etc.)
            tier: Tier (IRON, BRONZE, SILVER, GOLD, PLATINUM, DIAMOND)
            division: Division (I, II, III, IV)
            page: Page number (1-indexed)
            
        Returns:
            List of league entries
        """
        url = f"{self.base_url}/lol/league/v4/entries/{queue}/{tier}/{division}"
        params = {'page': page}
        result = self._request(url, params)
        return result if result else []
    
    def get_challenger_league(self, queue: str = 'RANKED_SOLO_5x5') -> Optional[Dict]:
        """Get Challenger league"""
        url = f"{self.base_url}/lol/league/v4/challengerleagues/by-queue/{queue}"
        return self._request(url)
    
    def get_grandmaster_league(self, queue: str = 'RANKED_SOLO_5x5') -> Optional[Dict]:
        """Get Grandmaster league"""
        url = f"{self.base_url}/lol/league/v4/grandmasterleagues/by-queue/{queue}"
        return self._request(url)
    
    def get_master_league(self, queue: str = 'RANKED_SOLO_5x5') -> Optional[Dict]:
        """Get Master league"""
        url = f"{self.base_url}/lol/league/v4/masterleagues/by-queue/{queue}"
        return self._request(url)
    
    def get_match_ids_by_puuid(self, puuid: str, start: int = 0, count: int = 20,
                               queue: Optional[int] = None, start_time: Optional[int] = None,
                               end_time: Optional[int] = None) -> List[str]:
        """
        Get match IDs for a summoner.
        
        Args:
            puuid: Player UUID
            start: Start index
            count: Number of matches (max 100)
            queue: Queue ID filter (420 for ranked solo/duo)
            start_time: Epoch timestamp (seconds)
            end_time: Epoch timestamp (seconds)
            
        Returns:
            List of match IDs
        """
        url = f"{self.regional_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        
        params = {'start': start, 'count': min(count, 100)}
        if queue:
            params['queue'] = queue
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        result = self._request(url, params)
        return result if result else []
    
    def get_match(self, match_id: str) -> Optional[Dict]:
        """
        Get detailed match data.
        
        Args:
            match_id: Match ID (e.g., 'NA1_4567890123')
            
        Returns:
            Match data dictionary
        """
        url = f"{self.regional_url}/lol/match/v5/matches/{match_id}"
        return self._request(url)
    
    def get_match_timeline(self, match_id: str) -> Optional[Dict]:
        """
        Get match timeline data.
        
        Args:
            match_id: Match ID
            
        Returns:
            Timeline data dictionary
        """
        url = f"{self.regional_url}/lol/match/v5/matches/{match_id}/timeline"
        return self._request(url)
    
    def get_current_patch(self) -> str:
        """
        Get current game version/patch.
        
        Returns:
            Patch version (e.g., '14.1')
        """
        try:
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            versions = response.json()
            
            if versions:
                # Return major.minor (e.g., '14.1' from '14.1.1')
                full_version = versions[0]
                parts = full_version.split('.')
                return f"{parts[0]}.{parts[1]}"
            
        except Exception as e:
            logger.warning(f"Failed to get patch from DDragon: {e}")
        
        # Fallback to a reasonable recent patch
        logger.warning("Using fallback patch version 15.21")
        return "15.21"
    
    def get_champion_data(self) -> Dict[str, Any]:
        """
        Get champion static data from Data Dragon.
        
        Returns:
            Champion data dictionary
        """
        try:
            patch = self.get_current_patch()
            url = f"https://ddragon.leagueoflegends.com/cdn/{patch}.1/data/en_US/champion.json"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get champion data: {e}")
            return {}
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

