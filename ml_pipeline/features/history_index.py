"""
Historical win-rate index for synergy and counter calculations.
Builds indices per ELO from collected match data.
"""

import numpy as np
import json
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class HistoryIndex:
    """
    Build and query historical win-rate indices for synergy and counter analysis.
    
    Indices:
    - Champion win rates per ELO
    - Champion pair co-occurrence win rates (synergy)
    - Champion vs champion win rates (counters)
    """
    
    def __init__(self, data_dir: str = "data/processed"):
        """
        Initialize history index.
        
        Args:
            data_dir: Directory containing processed match data
        """
        self.data_dir = Path(data_dir)
        
        # Per-ELO indices
        self.elo_indices = {}  # elo -> index data
        
        # Global statistics
        self.global_wr = {}  # champion_id -> win rate
        self.total_matches = 0
        
    def build_index(self, elo: Optional[str] = None):
        """
        Build historical indices from collected matches.
        
        Args:
            elo: Specific ELO to index (None = all ELOs)
        """
        if elo:
            self._build_elo_index(elo)
        else:
            # Build for all available ELOs
            for elo_file in self.data_dir.glob("matches_*.json"):
                elo_name = elo_file.stem.replace("matches_", "")
                self._build_elo_index(elo_name)
    
    def _build_elo_index(self, elo: str):
        """Build index for a specific ELO."""
        data_file = self.data_dir / f"matches_{elo}.json"
        
        if not data_file.exists():
            logger.warning(f"No data found for {elo}")
            return
        
        # Load matches
        with open(data_file, 'r') as f:
            matches = json.load(f)
        
        logger.info(f"Building index for {elo} from {len(matches)} matches...")
        
        # Initialize counters
        champ_wins = defaultdict(int)
        champ_games = defaultdict(int)
        
        # Pair synergy: (champ1, champ2) -> (wins, games)
        pair_wins = defaultdict(int)
        pair_games = defaultdict(int)
        
        # Counterpicks: (champ, enemy_champ) -> (wins, games)
        counter_wins = defaultdict(lambda: defaultdict(int))
        counter_games = defaultdict(lambda: defaultdict(int))
        
        # Process each match
        for match in matches:
            blue_win = match['blue_win']
            blue_picks = match['blue_picks']
            red_picks = match['red_picks']
            
            # Update champion win rates
            for champ in blue_picks:
                champ_games[champ] += 1
                if blue_win:
                    champ_wins[champ] += 1
            
            for champ in red_picks:
                champ_games[champ] += 1
                if not blue_win:
                    champ_wins[champ] += 1
            
            # Update pair synergies (teammates)
            self._update_pairs(blue_picks, blue_win, pair_wins, pair_games)
            self._update_pairs(red_picks, not blue_win, pair_wins, pair_games)
            
            # Update counterpicks (enemies)
            self._update_counters(blue_picks, red_picks, blue_win, counter_wins, counter_games)
            self._update_counters(red_picks, blue_picks, not blue_win, counter_wins, counter_games)
        
        # Calculate win rates
        champ_wr = {
            champ: champ_wins[champ] / champ_games[champ]
            for champ in champ_games if champ_games[champ] >= 5  # Min 5 games
        }
        
        pair_wr = {
            pair: pair_wins[pair] / pair_games[pair]
            for pair in pair_games if pair_games[pair] >= 3  # Min 3 games together
        }
        
        counter_wr = {}
        for champ in counter_games:
            counter_wr[champ] = {
                enemy: counter_wins[champ][enemy] / counter_games[champ][enemy]
                for enemy in counter_games[champ]
                if counter_games[champ][enemy] >= 3  # Min 3 games vs
            }
        
        # Store index
        self.elo_indices[elo] = {
            'champ_wr': champ_wr,
            'pair_wr': pair_wr,
            'counter_wr': counter_wr,
            'n_matches': len(matches),
            'avg_wr': np.mean(list(champ_wr.values())) if champ_wr else 0.5
        }
        
        logger.info(f"  ✓ Indexed {len(champ_wr)} champions, {len(pair_wr)} pairs, "
                   f"{sum(len(v) for v in counter_wr.values())} matchups")
        
        self.total_matches += len(matches)
    
    def _update_pairs(self, team: List[int], won: bool, 
                     pair_wins: Dict, pair_games: Dict):
        """Update pair synergy statistics."""
        for i, champ1 in enumerate(team):
            for champ2 in team[i+1:]:
                # Create canonical pair (sorted order)
                pair = tuple(sorted([champ1, champ2]))
                pair_games[pair] += 1
                if won:
                    pair_wins[pair] += 1
    
    def _update_counters(self, team: List[int], enemies: List[int], won: bool,
                        counter_wins: Dict, counter_games: Dict):
        """Update counterpick statistics."""
        for champ in team:
            for enemy in enemies:
                counter_games[champ][enemy] += 1
                if won:
                    counter_wins[champ][enemy] += 1
    
    def get_synergy(self, team: List[int], elo: str) -> float:
        """
        Calculate team synergy score based on historical co-win rates.
        
        Returns z-score normalized synergy: positive = better than expected.
        
        Args:
            team: List of 5 champion IDs
            elo: Rank tier
            
        Returns:
            Synergy z-score
        """
        if elo not in self.elo_indices:
            return 0.0
        
        index = self.elo_indices[elo]
        pair_wr = index['pair_wr']
        champ_wr = index['champ_wr']
        avg_wr = index['avg_wr']
        
        # Calculate expected vs actual pair win rates
        synergy_scores = []
        
        for i, champ1 in enumerate(team):
            for champ2 in team[i+1:]:
                pair = tuple(sorted([champ1, champ2]))
                
                if pair in pair_wr:
                    actual_wr = pair_wr[pair]
                    
                    # Expected WR = average of individual WRs
                    wr1 = champ_wr.get(champ1, avg_wr)
                    wr2 = champ_wr.get(champ2, avg_wr)
                    expected_wr = (wr1 + wr2) / 2
                    
                    # Synergy = actual - expected
                    synergy = actual_wr - expected_wr
                    synergy_scores.append(synergy)
        
        if not synergy_scores:
            return 0.0
        
        # Return mean synergy (already centered around 0)
        return float(np.mean(synergy_scores))
    
    def get_counter(self, blue_team: List[int], red_team: List[int], elo: str) -> float:
        """
        Calculate counterpick advantage for blue team vs red team.
        
        Positive = blue has advantage, negative = red has advantage.
        
        Args:
            blue_team: Blue team champion IDs
            red_team: Red team champion IDs
            elo: Rank tier
            
        Returns:
            Counter score (blue advantage)
        """
        if elo not in self.elo_indices:
            return 0.0
        
        index = self.elo_indices[elo]
        counter_wr = index['counter_wr']
        avg_wr = index['avg_wr']
        
        # Calculate blue team advantage
        blue_advantages = []
        
        for blue_champ in blue_team:
            for red_champ in red_team:
                # Blue vs Red matchup
                if blue_champ in counter_wr and red_champ in counter_wr[blue_champ]:
                    blue_wr = counter_wr[blue_champ][red_champ]
                    # Advantage = how much better than 50/50
                    advantage = blue_wr - 0.5
                    blue_advantages.append(advantage)
        
        if not blue_advantages:
            return 0.0
        
        # Return mean advantage
        return float(np.mean(blue_advantages))
    
    def save(self, filepath: str = "ml_pipeline/history_index.json"):
        """Save index to file."""
        # Convert defaultdicts to regular dicts for JSON serialization
        save_data = {}
        for elo, index in self.elo_indices.items():
            save_data[elo] = {
                'champ_wr': index['champ_wr'],
                'pair_wr': {f"{p[0]},{p[1]}": wr for p, wr in index['pair_wr'].items()},
                'counter_wr': {
                    str(c): {str(e): wr for e, wr in enemies.items()}
                    for c, enemies in index['counter_wr'].items()
                },
                'n_matches': index['n_matches'],
                'avg_wr': index['avg_wr']
            }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        logger.info(f"Saved history index to {filepath}")
    
    def load(self, filepath: str = "ml_pipeline/history_index.json"):
        """Load index from file."""
        with open(filepath, 'r') as f:
            save_data = json.load(f)
        
        for elo, index_data in save_data.items():
            # Convert string keys back to integers
            champ_wr = {int(k): v for k, v in index_data['champ_wr'].items()}
            
            pair_wr = {}
            for pair_str, wr in index_data['pair_wr'].items():
                c1, c2 = map(int, pair_str.split(','))
                pair_wr[(c1, c2)] = wr
            
            counter_wr = {}
            for champ_str, enemies in index_data['counter_wr'].items():
                champ = int(champ_str)
                counter_wr[champ] = {int(e): wr for e, wr in enemies.items()}
            
            self.elo_indices[elo] = {
                'champ_wr': champ_wr,
                'pair_wr': pair_wr,
                'counter_wr': counter_wr,
                'n_matches': index_data['n_matches'],
                'avg_wr': index_data['avg_wr']
            }
        
        self.total_matches = sum(idx['n_matches'] for idx in self.elo_indices.values())
        logger.info(f"Loaded history index from {filepath} ({self.total_matches} matches)")
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        return {
            'total_matches': self.total_matches,
            'elos_indexed': list(self.elo_indices.keys()),
            'per_elo_stats': {
                elo: {
                    'n_matches': idx['n_matches'],
                    'n_champions': len(idx['champ_wr']),
                    'n_pairs': len(idx['pair_wr']),
                    'n_matchups': sum(len(v) for v in idx['counter_wr'].values()),
                    'avg_wr': idx['avg_wr']
                }
                for elo, idx in self.elo_indices.items()
            }
        }


# Convenience functions
def get_synergy(team: List[int], elo: str, history_index: HistoryIndex) -> float:
    """
    Convenience wrapper for synergy calculation.
    
    Args:
        team: List of champion IDs
        elo: Rank tier
        history_index: HistoryIndex instance
        
    Returns:
        Synergy score
    """
    return history_index.get_synergy(team, elo)


def get_counter(blue_team: List[int], red_team: List[int], elo: str,
                history_index: HistoryIndex) -> float:
    """
    Convenience wrapper for counter calculation.
    
    Args:
        blue_team: Blue team champions
        red_team: Red team champions
        elo: Rank tier
        history_index: HistoryIndex instance
        
    Returns:
        Counter score (blue advantage)
    """
    return history_index.get_counter(blue_team, red_team, elo)


# ============================================================================
# Testing & Validation
# ============================================================================

if __name__ == '__main__':
    import sys
    
    print("="*70)
    print("History Index Test")
    print("="*70)
    
    # Build index
    print("\n1. Building history index...")
    history_idx = HistoryIndex()
    history_idx.build_index()
    
    stats = history_idx.get_stats()
    print(f"   ✓ Total matches: {stats['total_matches']}")
    print(f"   ✓ ELOs indexed: {stats['elos_indexed']}")
    
    if not stats['elos_indexed']:
        print("\n   ✗ No data found!")
        print("   Please run: python run_collector.py --ranks GOLD --matches-per-rank 50")
        sys.exit(1)
    
    # Show per-ELO stats
    print("\n2. Per-ELO statistics:")
    for elo, elo_stats in stats['per_elo_stats'].items():
        print(f"\n   {elo}:")
        print(f"   - Matches: {elo_stats['n_matches']}")
        print(f"   - Champions: {elo_stats['n_champions']}")
        print(f"   - Pairs: {elo_stats['n_pairs']}")
        print(f"   - Matchups: {elo_stats['n_matchups']}")
        print(f"   - Avg WR: {elo_stats['avg_wr']:.3f}")
    
    # Test synergy calculation
    if 'GOLD' in stats['elos_indexed']:
        print("\n3. Testing synergy calculation...")
        test_team = [10, 64, 103, 51, 412]  # Sample team
        synergy = history_idx.get_synergy(test_team, 'GOLD')
        print(f"   Team: {test_team}")
        print(f"   Synergy score: {synergy:.4f}")
        print(f"   Interpretation: {'Positive' if synergy > 0 else 'Negative'} synergy")
        
        # Test counter calculation
        print("\n4. Testing counter calculation...")
        blue_team = [10, 64, 103, 51, 412]
        red_team = [23, 11, 238, 22, 53]
        counter = history_idx.get_counter(blue_team, red_team, 'GOLD')
        print(f"   Blue: {blue_team}")
        print(f"   Red: {red_team}")
        print(f"   Counter score: {counter:.4f}")
        print(f"   Advantage: {'BLUE' if counter > 0 else 'RED'}")
    
    # Save index
    print("\n5. Saving history index...")
    history_idx.save()
    print(f"   ✓ Saved to ml_pipeline/history_index.json")
    
    print("\n" + "="*70)
    print("✅ History Index Test PASSED")
    print("="*70)


