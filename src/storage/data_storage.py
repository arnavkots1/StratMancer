"""
Storage handlers for match data in multiple formats.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from ..transformers.schema import MatchData

logger = logging.getLogger(__name__)


class DataStorage:
    """Handles saving and loading match data in various formats"""
    
    def __init__(self, base_path: str = "data", formats: List[str] = None):
        """
        Initialize storage handler.
        
        Args:
            base_path: Base directory for data storage
            formats: List of formats to save ('json', 'parquet')
        """
        self.base_path = Path(base_path)
        self.formats = formats or ['parquet', 'json']
        
        # Create directory structure
        self.raw_path = self.base_path / "raw"
        self.processed_path = self.base_path / "processed"
        
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Data storage initialized at {self.base_path}")
    
    def save_raw_match(self, match_id: str, raw_data: Dict):
        """
        Save raw API response for debugging.
        
        Args:
            match_id: Match identifier
            raw_data: Raw match data from API
        """
        try:
            file_path = self.raw_path / f"{match_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2)
            logger.debug(f"Saved raw match: {match_id}")
        except Exception as e:
            logger.error(f"Failed to save raw match {match_id}: {e}")
    
    def save_matches(self, matches: List[MatchData], rank: str = "all"):
        """
        Save processed matches in configured formats.
        
        Args:
            matches: List of MatchData objects
            rank: Rank tier for filename
        """
        if not matches:
            logger.warning("No matches to save")
            return
        
        # Convert to dictionaries
        match_dicts = [match.model_dump() for match in matches]
        
        # Save in each format
        if 'json' in self.formats:
            self._save_json(match_dicts, rank)
        
        if 'parquet' in self.formats:
            self._save_parquet(match_dicts, rank)
    
    def _save_json(self, matches: List[Dict], rank: str):
        """Save matches as JSON"""
        try:
            file_path = self.processed_path / f"matches_{rank}.json"
            
            # Load existing if present
            existing = []
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            
            # Merge (avoid duplicates by match_id)
            existing_ids = {m['match_id'] for m in existing}
            new_matches = [m for m in matches if m['match_id'] not in existing_ids]
            
            all_matches = existing + new_matches
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_matches, f, indent=2)
            
            logger.info(f"Saved {len(new_matches)} matches to JSON ({rank})")
            
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
    
    def _save_parquet(self, matches: List[Dict], rank: str):
        """Save matches as Parquet"""
        try:
            file_path = self.processed_path / f"matches_{rank}.parquet"
            
            # Flatten nested structures for Parquet
            flattened = self._flatten_matches(matches)
            
            # Convert to DataFrame
            df = pd.DataFrame(flattened)
            
            # Load existing if present
            if file_path.exists():
                existing_df = pd.read_parquet(file_path)
                
                # Merge and remove duplicates
                df = pd.concat([existing_df, df], ignore_index=True)
                df = df.drop_duplicates(subset=['match_id'], keep='last')
            
            # Save with compression
            df.to_parquet(file_path, compression='snappy', index=False)
            
            logger.info(f"Saved {len(matches)} matches to Parquet ({rank})")
            
        except Exception as e:
            logger.error(f"Failed to save Parquet: {e}")
    
    def _flatten_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Flatten nested structures for Parquet storage.
        Converts lists and nested objects to string representations or separate columns.
        """
        flattened = []
        
        for match in matches:
            flat = {
                'match_id': match['match_id'],
                'patch': match['patch'],
                'elo_rank': match['elo_rank'],
                'blue_win': match['blue_win'],
                
                # Store picks/bans as JSON strings
                'blue_picks': json.dumps(match['blue_picks']),
                'red_picks': json.dumps(match['red_picks']),
                'blue_bans': json.dumps(match['blue_bans']),
                'red_bans': json.dumps(match['red_bans']),
                
                # Objectives
                'blue_dragons': match['blue_objectives']['dragons'],
                'blue_heralds': match['blue_objectives']['heralds'],
                'blue_barons': match['blue_objectives']['barons'],
                'blue_towers': match['blue_objectives']['towers'],
                
                'red_dragons': match['red_objectives']['dragons'],
                'red_heralds': match['red_objectives']['heralds'],
                'red_barons': match['red_objectives']['barons'],
                'red_towers': match['red_objectives']['towers'],
                
                # Derived features
                'ap_ad_ratio': match['derived_features']['ap_ad_ratio'],
                'engage_score': match['derived_features']['engage_score'],
                'splitpush_score': match['derived_features']['splitpush_score'],
                'teamfight_synergy': match['derived_features']['teamfight_synergy'],
                
                # Champion stats as JSON string
                'champion_stats': json.dumps(match['champion_stats'])
            }
            
            flattened.append(flat)
        
        return flattened
    
    def load_matches(self, rank: str = "all", format: str = "parquet") -> List[MatchData]:
        """
        Load matches from storage.
        
        Args:
            rank: Rank tier to load
            format: Format to load from ('json' or 'parquet')
            
        Returns:
            List of MatchData objects
        """
        try:
            if format == 'json':
                return self._load_json(rank)
            elif format == 'parquet':
                return self._load_parquet(rank)
            else:
                raise ValueError(f"Unknown format: {format}")
        except Exception as e:
            logger.error(f"Failed to load matches: {e}")
            return []
    
    def _load_json(self, rank: str) -> List[MatchData]:
        """Load matches from JSON"""
        file_path = self.processed_path / f"matches_{rank}.json"
        
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            match_dicts = json.load(f)
        
        matches = [MatchData(**m) for m in match_dicts]
        return matches
    
    def _load_parquet(self, rank: str) -> List[MatchData]:
        """Load matches from Parquet"""
        file_path = self.processed_path / f"matches_{rank}.parquet"
        
        if not file_path.exists():
            return []
        
        df = pd.read_parquet(file_path)
        
        # Unflatten and convert to MatchData
        matches = []
        for _, row in df.iterrows():
            match_dict = self._unflatten_row(row)
            matches.append(MatchData(**match_dict))
        
        return matches
    
    def _unflatten_row(self, row: pd.Series) -> Dict:
        """Unflatten a Parquet row back to match dictionary"""
        return {
            'match_id': row['match_id'],
            'patch': row['patch'],
            'elo_rank': row['elo_rank'],
            'blue_win': row['blue_win'],
            'blue_picks': json.loads(row['blue_picks']),
            'red_picks': json.loads(row['red_picks']),
            'blue_bans': json.loads(row['blue_bans']),
            'red_bans': json.loads(row['red_bans']),
            'blue_objectives': {
                'dragons': int(row['blue_dragons']),
                'heralds': int(row['blue_heralds']),
                'barons': int(row['blue_barons']),
                'towers': int(row['blue_towers'])
            },
            'red_objectives': {
                'dragons': int(row['red_dragons']),
                'heralds': int(row['red_heralds']),
                'barons': int(row['red_barons']),
                'towers': int(row['red_towers'])
            },
            'derived_features': {
                'ap_ad_ratio': float(row['ap_ad_ratio']),
                'engage_score': float(row['engage_score']),
                'splitpush_score': float(row['splitpush_score']),
                'teamfight_synergy': float(row['teamfight_synergy'])
            },
            'champion_stats': json.loads(row['champion_stats'])
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics about stored data"""
        stats = {
            'total_matches': 0,
            'by_rank': {},
            'by_patch': {}
        }
        
        # Count matches in processed directory
        for file_path in self.processed_path.glob("matches_*.parquet"):
            try:
                df = pd.read_parquet(file_path)
                rank = file_path.stem.replace('matches_', '')
                count = len(df)
                
                stats['by_rank'][rank] = count
                stats['total_matches'] += count
                
                # Count by patch
                if 'patch' in df.columns:
                    patch_counts = df['patch'].value_counts().to_dict()
                    for patch, cnt in patch_counts.items():
                        stats['by_patch'][patch] = stats['by_patch'].get(patch, 0) + cnt
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
        
        return stats

