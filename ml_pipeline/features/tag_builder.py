"""
Champion Tag Builder for StratMancer ML Pipeline

Generates comprehensive champion tags by:
1. Scanning collected match data
2. Fetching static champion data from Riot API
3. Computing derived features (role frequency, damage type, etc.)
4. Applying manual overrides from YAML
5. Enriching with API data (mastery, challenges) if available

Usage:
    python -m ml_pipeline.features.tag_builder \
        --data_dir ./data \
        --out ./ml_pipeline/feature_map.json \
        --overrides ./ml_pipeline/tags_overrides.yaml
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import httpx
import pandas as pd
import yaml
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.config_manager import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChampionTagBuilder:
    """Builds comprehensive champion tags from data and API"""
    
    # Default champion tags (heuristic-based, can be overridden)
    DEFAULT_TAGS = {
        'role': 'UNKNOWN',
        'damage': 'Mix',
        'engage': 1,
        'hard_cc': 1,
        'poke': 1,
        'splitpush': 1,
        'scaling_early': 1,
        'scaling_mid': 2,
        'scaling_late': 2,
        'frontline': 1,
        'skill_cap': 2,
        'comfort_score': 0,
        'experience_index': 0
    }
    
    # Role mapping
    ROLE_MAP = {
        'TOP': 'Top',
        'JUNGLE': 'Jgl',
        'MIDDLE': 'Mid',
        'MID': 'Mid',
        'BOTTOM': 'ADC',
        'UTILITY': 'Sup',
        'SUPPORT': 'Sup'
    }
    
    def __init__(self, data_dir: str, overrides_path: Optional[str] = None):
        """
        Initialize tag builder.
        
        Args:
            data_dir: Directory containing match data (parquet/json)
            overrides_path: Optional path to YAML overrides file
        """
        self.data_dir = Path(data_dir)
        self.overrides_path = Path(overrides_path) if overrides_path else None
        self.overrides = self._load_overrides()
        
        # Champion data
        self.champion_ids: Set[int] = set()
        self.champion_names: Dict[int, str] = {}
        self.champion_roles: Dict[int, Counter] = defaultdict(Counter)
        self.champion_damage_types: Dict[int, Dict] = {}
        
        # API client
        self.config = get_config()
        self.api_key = None
        try:
            self.api_key = self.config.get_riot_api_key()
        except:
            logger.warning("No API key found - will use static data only")
        
        self.region = self.config.get_region()
        self.current_patch = None
    
    def _load_overrides(self) -> Dict:
        """Load manual overrides from YAML"""
        if not self.overrides_path or not self.overrides_path.exists():
            return {}
        
        try:
            with open(self.overrides_path, 'r') as f:
                overrides = yaml.safe_load(f) or {}
            logger.info(f"Loaded {len(overrides)} override(s) from {self.overrides_path}")
            return overrides
        except Exception as e:
            logger.error(f"Failed to load overrides: {e}")
            return {}
    
    async def fetch_champion_data(self) -> Dict:
        """Fetch champion static data from Riot API"""
        try:
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                versions = response.json()
                patch = versions[0]
                self.current_patch = '.'.join(patch.split('.')[:2])
                
                # Get champion data
                champ_url = f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json"
                response = await client.get(champ_url, timeout=10)
                data = response.json()
                
                # Build champion ID to name mapping
                champ_data = {}
                for name, info in data['data'].items():
                    champ_id = int(info['key'])
                    champ_data[champ_id] = {
                        'name': info['name'],
                        'id': champ_id,
                        'title': info['title'],
                        'tags': info['tags'],  # e.g., ['Fighter', 'Tank']
                        'partype': info['partype']  # Mana, Energy, etc.
                    }
                
                logger.info(f"Fetched {len(champ_data)} champions from Data Dragon (patch {patch})")
                return champ_data
                
        except Exception as e:
            logger.error(f"Failed to fetch champion data: {e}")
            return {}
    
    def scan_data_files(self):
        """Scan data directory for champion IDs and usage patterns"""
        logger.info(f"Scanning data directory: {self.data_dir}")
        
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return
        
        # Scan parquet files
        parquet_files = list(self.data_dir.glob("**/*.parquet"))
        json_files = list(self.data_dir.glob("**/*.json"))
        
        logger.info(f"Found {len(parquet_files)} parquet files, {len(json_files)} JSON files")
        
        for pq_file in parquet_files:
            try:
                df = pd.read_parquet(pq_file)
                self._extract_from_dataframe(df)
            except Exception as e:
                logger.error(f"Failed to read {pq_file}: {e}")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for match in data:
                        self._extract_from_match(match)
                else:
                    self._extract_from_match(data)
            except Exception as e:
                logger.error(f"Failed to read {json_file}: {e}")
        
        logger.info(f"Found {len(self.champion_ids)} unique champions in data")
    
    def _extract_from_dataframe(self, df: pd.DataFrame):
        """Extract champion info from DataFrame"""
        for _, row in df.iterrows():
            try:
                # Extract picks
                if 'blue_picks' in row:
                    picks = json.loads(row['blue_picks']) if isinstance(row['blue_picks'], str) else row['blue_picks']
                    self.champion_ids.update(picks)
                
                if 'red_picks' in row:
                    picks = json.loads(row['red_picks']) if isinstance(row['red_picks'], str) else row['red_picks']
                    self.champion_ids.update(picks)
                
                # Extract champion stats (includes roles)
                if 'champion_stats' in row:
                    stats = json.loads(row['champion_stats']) if isinstance(row['champion_stats'], str) else row['champion_stats']
                    for champ_stat in stats:
                        champ_id = champ_stat.get('id')
                        role = champ_stat.get('role', 'UNKNOWN')
                        if champ_id:
                            self.champion_ids.add(champ_id)
                            self.champion_roles[champ_id][role] += 1
            except Exception as e:
                logger.debug(f"Error extracting from row: {e}")
    
    def _extract_from_match(self, match: Dict):
        """Extract champion info from match dictionary"""
        try:
            # Extract picks
            self.champion_ids.update(match.get('blue_picks', []))
            self.champion_ids.update(match.get('red_picks', []))
            
            # Extract champion stats
            for champ_stat in match.get('champion_stats', []):
                champ_id = champ_stat.get('id')
                role = champ_stat.get('role', 'UNKNOWN')
                if champ_id:
                    self.champion_ids.add(champ_id)
                    self.champion_roles[champ_id][role] += 1
        except Exception as e:
            logger.debug(f"Error extracting from match: {e}")
    
    def _infer_role(self, champ_id: int, champ_info: Dict) -> str:
        """Infer primary role for champion"""
        # First check observed data
        if champ_id in self.champion_roles and self.champion_roles[champ_id]:
            most_common_role = self.champion_roles[champ_id].most_common(1)[0][0]
            return self.ROLE_MAP.get(most_common_role, 'UNKNOWN')
        
        # Fallback to champion tags from Riot API
        tags = champ_info.get('tags', [])
        if 'Marksman' in tags:
            return 'ADC'
        elif 'Support' in tags:
            return 'Sup'
        elif 'Assassin' in tags or 'Mage' in tags:
            return 'Mid'
        elif 'Tank' in tags or 'Fighter' in tags:
            return 'Top'
        
        return 'UNKNOWN'
    
    def _infer_damage_type(self, champ_info: Dict) -> str:
        """Infer primary damage type"""
        tags = champ_info.get('tags', [])
        partype = champ_info.get('partype', '')
        
        if 'Mage' in tags or partype == 'Mana' and 'Marksman' not in tags:
            return 'AP'
        elif 'Marksman' in tags or 'Assassin' in tags:
            return 'AD'
        else:
            return 'Mix'
    
    def _generate_heuristic_tags(self, champ_id: int, champ_info: Dict) -> Dict:
        """Generate heuristic tags based on champion data"""
        tags = champ_info.get('tags', [])
        role = self._infer_role(champ_id, champ_info)
        damage = self._infer_damage_type(champ_info)
        
        # Heuristics based on champion class
        engage = 1
        hard_cc = 1
        poke = 1
        splitpush = 1
        scaling_early = 2
        scaling_mid = 2
        scaling_late = 2
        frontline = 1
        skill_cap = 2
        
        if 'Tank' in tags:
            engage = 2
            hard_cc = 2
            frontline = 3
            scaling_late = 3
        
        if 'Fighter' in tags:
            splitpush = 2
            scaling_mid = 3
            frontline = 2
        
        if 'Assassin' in tags:
            engage = 2
            scaling_early = 3
            skill_cap = 3
        
        if 'Mage' in tags:
            poke = 3
            scaling_late = 3
            skill_cap = 2
        
        if 'Marksman' in tags:
            scaling_late = 3
            poke = 2
            skill_cap = 2
        
        if 'Support' in tags:
            hard_cc = 2
            poke = 2
            frontline = 1
            scaling_early = 2
        
        return {
            'role': role,
            'damage': damage,
            'engage': engage,
            'hard_cc': hard_cc,
            'poke': poke,
            'splitpush': splitpush,
            'scaling_early': scaling_early,
            'scaling_mid': scaling_mid,
            'scaling_late': scaling_late,
            'frontline': frontline,
            'skill_cap': skill_cap,
            'comfort_score': 0,
            'experience_index': 0
        }
    
    async def build_tags(self) -> Dict:
        """Build complete tag dataset"""
        logger.info("Building champion tags...")
        
        # Fetch champion data from API
        champ_data = await self.fetch_champion_data()
        
        # Scan local data
        self.scan_data_files()
        
        # If no champions found in data, use all from API
        if not self.champion_ids and champ_data:
            self.champion_ids = set(champ_data.keys())
            logger.info(f"No local data found, using all {len(self.champion_ids)} champions from API")
        
        # Build tags for each champion
        tags_output = {}
        champ_index = {}
        id_to_index = {}  # Champion ID -> array index mapping
        
        for idx, champ_id in enumerate(sorted(self.champion_ids), start=0):
            champ_info = champ_data.get(champ_id, {})
            champ_name = champ_info.get('name', f'Champion_{champ_id}')
            
            # Generate heuristic tags
            if champ_info:
                tags = self._generate_heuristic_tags(champ_id, champ_info)
            else:
                tags = self.DEFAULT_TAGS.copy()
                logger.warning(f"No data for champion {champ_id}, using defaults")
            
            # Apply overrides
            if champ_id in self.overrides:
                override = self.overrides[champ_id]
                tags.update(override)
                logger.info(f"Applied override for {champ_name} ({champ_id})")
            
            tags_output[str(champ_id)] = tags
            champ_index[champ_name] = champ_id
            id_to_index[str(champ_id)] = idx  # Map ID to sequential index
        
        return {
            'champ_index': champ_index,
            'id_to_index': id_to_index,
            'tags': tags_output,
            'meta': {
                'num_champ': len(tags_output),
                'version': 'v1',
                'generated': datetime.now().isoformat(),
                'patch': self.current_patch or 'unknown',
                'source': 'RiotAPI + LocalData',
                'data_dir': str(self.data_dir),
                'overrides_applied': len(self.overrides)
            }
        }
    
    def save_feature_map(self, output_path: str, feature_map: Dict):
        """Save feature map to JSON"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(feature_map, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved feature map to {output_path}")
        logger.info(f"  Champions: {feature_map['meta']['num_champ']}")
        logger.info(f"  Patch: {feature_map['meta']['patch']}")
        logger.info(f"  Overrides: {feature_map['meta']['overrides_applied']}")
    
    def create_default_overrides(self, output_path: str):
        """Create example overrides file"""
        output_path = Path(output_path)
        
        if output_path.exists():
            logger.info(f"Overrides file already exists: {output_path}")
            return
        
        example_overrides = {
            266: {  # Aatrox
                'role': 'Top',
                'damage': 'AD',
                'engage': 2,
                'hard_cc': 1,
                'poke': 0,
                'splitpush': 2,
                'scaling_early': 2,
                'scaling_mid': 3,
                'scaling_late': 3,
                'frontline': 2,
                'skill_cap': 3
            },
            # Add more examples here
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(example_overrides, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Created example overrides file: {output_path}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Build champion tags for ML pipeline'
    )
    parser.add_argument(
        '--data_dir',
        type=str,
        default='./data',
        help='Directory containing match data'
    )
    parser.add_argument(
        '--out',
        type=str,
        default='./ml_pipeline/feature_map.json',
        help='Output path for feature map'
    )
    parser.add_argument(
        '--overrides',
        type=str,
        default='./ml_pipeline/tags_overrides.yaml',
        help='Path to overrides YAML file'
    )
    parser.add_argument(
        '--create-overrides',
        action='store_true',
        help='Create example overrides file and exit'
    )
    
    args = parser.parse_args()
    
    # Create builder
    builder = ChampionTagBuilder(
        data_dir=args.data_dir,
        overrides_path=args.overrides
    )
    
    # Create overrides if requested
    if args.create_overrides:
        builder.create_default_overrides(args.overrides)
        return 0
    
    # Build tags
    start_time = time.time()
    feature_map = await builder.build_tags()
    elapsed = time.time() - start_time
    
    # Save output
    builder.save_feature_map(args.out, feature_map)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Champion Tag Builder - Summary")
    print("=" * 60)
    print(f"Total champions tagged: {feature_map['meta']['num_champ']}")
    print(f"Current patch: {feature_map['meta']['patch']}")
    print(f"Overrides applied: {feature_map['meta']['overrides_applied']}")
    print(f"Runtime: {elapsed:.2f}s")
    print(f"Output: {args.out}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))


