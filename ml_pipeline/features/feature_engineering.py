"""
Feature engineering pipeline for draft prediction.
Converts match JSON/Parquet into fixed-length ML vectors.
"""

import numpy as np
import json
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path


def load_feature_map(feature_map_path: str = "ml_pipeline/feature_map.json") -> Dict:
    """Load the feature map containing champion tags and metadata."""
    with open(feature_map_path, 'r') as f:
        return json.load(f)


def build_role_onehots(match: Dict, feature_map: Dict) -> np.ndarray:
    """
    Encode champion picks as role-based one-hot vectors.
    
    Creates a matrix: 5 roles × N champions × 2 teams (blue/red)
    
    Args:
        match: Match data dictionary
        feature_map: Feature map with champion tags
        
    Returns:
        Flattened one-hot array for all role×champion combinations
    """
    roles = ['Top', 'Jgl', 'Mid', 'ADC', 'Sup']
    num_champs = feature_map['meta']['num_champ']
    
    # Initialize: 2 teams × 5 roles × num_champs
    role_matrix = np.zeros((2, 5, num_champs), dtype=np.float32)
    
    tags = feature_map['tags']
    id_to_index = feature_map.get('id_to_index', {})
    
    # Process blue team
    for champ_id in match['blue_picks']:
        champ_str = str(champ_id)
        if champ_str in tags and champ_str in id_to_index:
            role = tags[champ_str]['role']
            if role in roles:
                role_idx = roles.index(role)
                champ_idx = id_to_index[champ_str]  # Use mapped index
                role_matrix[0, role_idx, champ_idx] = 1.0
    
    # Process red team
    for champ_id in match['red_picks']:
        champ_str = str(champ_id)
        if champ_str in tags and champ_str in id_to_index:
            role = tags[champ_str]['role']
            if role in roles:
                role_idx = roles.index(role)
                champ_idx = id_to_index[champ_str]  # Use mapped index
                role_matrix[1, role_idx, champ_idx] = 1.0
    
    # Flatten: [blue_top_champs, blue_jgl_champs, ..., red_top_champs, ...]
    return role_matrix.flatten()


def build_ban_onehots(match: Dict, feature_map: Dict) -> np.ndarray:
    """
    Encode bans as one-hot vectors.
    
    Args:
        match: Match data dictionary
        feature_map: Feature map with champion metadata
        
    Returns:
        One-hot array for bans (2 teams × 5 bans × num_champs)
    """
    num_champs = feature_map['meta']['num_champ']
    id_to_index = feature_map.get('id_to_index', {})
    
    # 2 teams × 5 bans × num_champs
    ban_matrix = np.zeros((2, 5, num_champs), dtype=np.float32)
    
    # Process blue bans
    blue_bans = match.get('blue_bans', [])
    for i, ban_id in enumerate(blue_bans[:5]):  # Max 5 bans
        ban_str = str(ban_id)
        if ban_id > 0 and ban_str in id_to_index:  # -1 means no ban
            champ_idx = id_to_index[ban_str]
            ban_matrix[0, i, champ_idx] = 1.0
    
    # Process red bans
    red_bans = match.get('red_bans', [])
    for i, ban_id in enumerate(red_bans[:5]):  # Max 5 bans
        ban_str = str(ban_id)
        if ban_id > 0 and ban_str in id_to_index:  # -1 means no ban
            champ_idx = id_to_index[ban_str]
            ban_matrix[1, i, champ_idx] = 1.0
    
    return ban_matrix.flatten()


def comp_shape_features(match: Dict, feature_map: Dict) -> Dict[str, float]:
    """
    Calculate team composition shape features.
    
    Features:
    - ap_ad_ratio: AP vs AD damage split
    - engage_score: Team initiation potential
    - cc_score: Crowd control capability
    - poke_score: Poke/harass potential
    - splitpush_score: Splitpush threat
    - frontline_score: Tankiness/frontline
    - scaling_early/mid/late: Power curve
    - role_balance_distance: How well roles are covered
    - skill_cap_sum: Mechanical difficulty
    
    Args:
        match: Match data dictionary
        feature_map: Feature map with champion tags
        
    Returns:
        Dictionary of composition features for both teams
    """
    tags = feature_map['tags']
    
    def calc_team_features(picks: List[int], prefix: str) -> Dict[str, float]:
        """Calculate features for one team."""
        features = {}
        
        # Initialize counters
        ap_count = 0
        ad_count = 0
        engage_sum = 0
        cc_sum = 0
        poke_sum = 0
        splitpush_sum = 0
        frontline_sum = 0
        early_sum = 0
        mid_sum = 0
        late_sum = 0
        skill_cap_sum = 0
        
        # Count role coverage
        roles_covered = set()
        
        for champ_id in picks:
            champ_str = str(champ_id)
            if champ_str not in tags:
                continue
            
            tag = tags[champ_str]
            
            # Damage type
            if tag['damage'] == 'AP':
                ap_count += 1
            elif tag['damage'] == 'AD':
                ad_count += 1
            else:  # Mix
                ap_count += 0.5
                ad_count += 0.5
            
            # Accumulate scores
            engage_sum += tag.get('engage', 0)
            cc_sum += tag.get('hard_cc', 0)
            poke_sum += tag.get('poke', 0)
            splitpush_sum += tag.get('splitpush', 0)
            frontline_sum += tag.get('frontline', 0)
            early_sum += tag.get('scaling_early', 0)
            mid_sum += tag.get('scaling_mid', 0)
            late_sum += tag.get('scaling_late', 0)
            skill_cap_sum += tag.get('skill_cap', 0)
            
            # Track role
            roles_covered.add(tag['role'])
        
        # Calculate ratios and averages
        total_dmg = ap_count + ad_count
        features[f'{prefix}_ap_ad_ratio'] = ap_count / total_dmg if total_dmg > 0 else 0.5
        
        # Average scores (normalized to 0-1 scale, max is 3)
        n_picks = len(picks) if len(picks) > 0 else 1
        features[f'{prefix}_engage_score'] = engage_sum / (n_picks * 3)
        features[f'{prefix}_cc_score'] = cc_sum / (n_picks * 3)
        features[f'{prefix}_poke_score'] = poke_sum / (n_picks * 3)
        features[f'{prefix}_splitpush_score'] = splitpush_sum / (n_picks * 3)
        features[f'{prefix}_frontline_score'] = frontline_sum / (n_picks * 3)
        features[f'{prefix}_scaling_early'] = early_sum / (n_picks * 3)
        features[f'{prefix}_scaling_mid'] = mid_sum / (n_picks * 3)
        features[f'{prefix}_scaling_late'] = late_sum / (n_picks * 3)
        features[f'{prefix}_skill_cap_sum'] = skill_cap_sum / (n_picks * 3)
        
        # Role balance: distance from ideal (all 5 roles covered)
        features[f'{prefix}_role_balance'] = len(roles_covered) / 5.0
        
        return features
    
    # Calculate for both teams
    blue_features = calc_team_features(match['blue_picks'], 'blue')
    red_features = calc_team_features(match['red_picks'], 'red')
    
    # Combine
    all_features = {**blue_features, **red_features}
    
    # Add relative features (blue advantage)
    all_features['engage_diff'] = blue_features['blue_engage_score'] - red_features['red_engage_score']
    all_features['cc_diff'] = blue_features['blue_cc_score'] - red_features['red_cc_score']
    all_features['poke_diff'] = blue_features['blue_poke_score'] - red_features['red_poke_score']
    all_features['splitpush_diff'] = blue_features['blue_splitpush_score'] - red_features['red_splitpush_score']
    all_features['frontline_diff'] = blue_features['blue_frontline_score'] - red_features['red_frontline_score']
    all_features['early_diff'] = blue_features['blue_scaling_early'] - red_features['red_scaling_early']
    all_features['mid_diff'] = blue_features['blue_scaling_mid'] - red_features['red_scaling_mid']
    all_features['late_diff'] = blue_features['blue_scaling_late'] - red_features['red_scaling_late']
    
    return all_features


def patch_features(patch_str: str) -> np.ndarray:
    """
    Encode patch version as ordinal + one-hot season.
    
    Args:
        patch_str: Patch string like "15.20"
        
    Returns:
        Array with [season_ordinal, minor_ordinal]
    """
    try:
        parts = patch_str.split('.')
        season = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        
        # Normalize season (S11 = 11, S15 = 15, etc.)
        # Use relative to S14 (2024) as baseline
        season_norm = (season - 14) / 10.0  # -0.3 for S11, 0.1 for S15
        minor_norm = minor / 24.0  # Normalize to 0-1 (max 24 patches/year)
        
        return np.array([season_norm, minor_norm], dtype=np.float32)
    except:
        # Default for unknown/invalid patches
        return np.array([0.0, 0.0], dtype=np.float32)


def assemble_features(
    match: Dict,
    elo: str,
    feature_map: Optional[Dict] = None,
    history_index: Optional[Any] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Assemble complete feature vector from match data.
    
    This is the main entry point that combines all feature types into
    a single fixed-length vector suitable for ML models.
    
    Args:
        match: Match data dictionary
        elo: Rank tier (IRON, BRONZE, ..., CHALLENGER)
        feature_map: Feature map (loaded if None)
        history_index: Historical win rate index (optional)
        
    Returns:
        Tuple of:
        - X_vec: Feature vector (numpy array)
        - named: Dictionary with named features for interpretability
    """
    # Load feature map if not provided
    if feature_map is None:
        feature_map = load_feature_map()
    
    # 1. Role-based one-hots (champion picks by role)
    role_onehots = build_role_onehots(match, feature_map)
    
    # 2. Ban one-hots
    ban_onehots = build_ban_onehots(match, feature_map)
    
    # 3. Composition shape features
    comp_features = comp_shape_features(match, feature_map)
    comp_vector = np.array(list(comp_features.values()), dtype=np.float32)
    
    # 4. Patch features
    patch_vector = patch_features(match.get('patch', '15.20'))
    
    # 5. ELO encoding (one-hot)
    elo_ranks = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 
                 'EMERALD', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
    elo_onehot = np.zeros(len(elo_ranks), dtype=np.float32)
    if elo.upper() in elo_ranks:
        elo_onehot[elo_ranks.index(elo.upper())] = 1.0
    
    # 6. Historical features (synergy + counter)
    if history_index is not None:
        try:
            synergy_blue = history_index.get_synergy(match['blue_picks'], elo)
            synergy_red = history_index.get_synergy(match['red_picks'], elo)
            counter_score = history_index.get_counter(
                match['blue_picks'], 
                match['red_picks'], 
                elo
            )
            history_vector = np.array([synergy_blue, synergy_red, counter_score], dtype=np.float32)
        except:
            history_vector = np.zeros(3, dtype=np.float32)
    else:
        history_vector = np.zeros(3, dtype=np.float32)
    
    # 7. Objective features (if available in derived_features)
    derived = match.get('derived_features', {})
    objectives_vector = np.array([
        derived.get('ap_ad_ratio', comp_features.get('blue_ap_ad_ratio', 0.5)),
        derived.get('engage_score', comp_features.get('blue_engage_score', 0.5)),
        derived.get('splitpush_score', comp_features.get('blue_splitpush_score', 0.5)),
        derived.get('teamfight_synergy', 0.5)  # Placeholder
    ], dtype=np.float32)
    
    # Concatenate all features
    X_vec = np.concatenate([
        role_onehots,           # Role-based champion encoding
        ban_onehots,            # Ban encoding
        comp_vector,            # Composition features
        patch_vector,           # Patch version
        elo_onehot,             # Rank tier
        history_vector,         # Synergy + counter
        objectives_vector       # Objective-based features
    ])
    
    # Create named features dictionary for interpretability
    named = {
        'match_id': match.get('match_id', 'unknown'),
        'patch': match.get('patch', 'unknown'),
        'elo': elo,
        'blue_picks': match['blue_picks'],
        'red_picks': match['red_picks'],
        'blue_win': match.get('blue_win', None),
        'n_role_features': len(role_onehots),
        'n_ban_features': len(ban_onehots),
        'n_comp_features': len(comp_vector),
        'comp_features': comp_features,
        'total_features': len(X_vec)
    }
    
    return X_vec, named


# ============================================================================
# Testing & Validation
# ============================================================================

if __name__ == '__main__':
    import time
    import sys
    from pathlib import Path
    
    print("="*70)
    print("Feature Engineering Pipeline Test")
    print("="*70)
    
    # Load feature map
    print("\n1. Loading feature map...")
    feature_map = load_feature_map()
    print(f"   ✓ Loaded {feature_map['meta']['num_champ']} champions")
    print(f"   ✓ Patch: {feature_map['meta']['patch']}")
    print(f"   ✓ Overrides: {feature_map['meta']['overrides_applied']}")
    
    # Load sample matches
    print("\n2. Loading sample matches...")
    data_path = Path("data/processed/matches_GOLD.json")
    
    if not data_path.exists():
        print(f"   ✗ No data found at {data_path}")
        print("   Please run: python run_collector.py --ranks GOLD --matches-per-rank 10")
        sys.exit(1)
    
    with open(data_path, 'r') as f:
        matches = json.load(f)
    
    print(f"   ✓ Loaded {len(matches)} matches")
    
    # Test feature assembly on first 5 matches
    print("\n3. Testing feature assembly...")
    test_count = min(5, len(matches))
    
    feature_vectors = []
    timings = []
    
    for i, match in enumerate(matches[:test_count]):
        start_time = time.time()
        X_vec, named = assemble_features(match, 'GOLD', feature_map)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        feature_vectors.append(X_vec)
        timings.append(elapsed)
        
        if i == 0:
            print(f"\n   Match {i+1}: {named['match_id']}")
            print(f"   - Blue picks: {named['blue_picks']}")
            print(f"   - Red picks: {named['red_picks']}")
            print(f"   - Winner: {'BLUE' if named['blue_win'] else 'RED'}")
            print(f"   - Feature vector shape: {X_vec.shape}")
            print(f"   - Total features: {named['total_features']}")
            print(f"   - Role features: {named['n_role_features']}")
            print(f"   - Ban features: {named['n_ban_features']}")
            print(f"   - Comp features: {named['n_comp_features']}")
            print(f"   - Processing time: {elapsed:.2f}ms")
    
    # Verify consistency
    print("\n4. Verifying feature consistency...")
    shapes = [vec.shape for vec in feature_vectors]
    all_same = all(s == shapes[0] for s in shapes)
    
    if all_same:
        print(f"   ✓ All vectors have same shape: {shapes[0]}")
    else:
        print(f"   ✗ Inconsistent shapes: {shapes}")
        sys.exit(1)
    
    # Performance check
    avg_time = np.mean(timings)
    print(f"\n5. Performance metrics:")
    print(f"   - Average processing time: {avg_time:.2f}ms")
    print(f"   - Max processing time: {max(timings):.2f}ms")
    print(f"   - Min processing time: {min(timings):.2f}ms")
    
    if avg_time <= 5.0:
        print(f"   ✓ Performance target met (<5ms)")
    else:
        print(f"   ⚠ Performance target missed (target: <5ms, actual: {avg_time:.2f}ms)")
    
    # Sample composition features
    print(f"\n6. Sample composition features (Match 1):")
    _, named = assemble_features(matches[0], 'GOLD', feature_map)
    comp = named['comp_features']
    print(f"   Blue team:")
    print(f"   - AP/AD ratio: {comp['blue_ap_ad_ratio']:.2f}")
    print(f"   - Engage score: {comp['blue_engage_score']:.2f}")
    print(f"   - CC score: {comp['blue_cc_score']:.2f}")
    print(f"   - Poke score: {comp['blue_poke_score']:.2f}")
    print(f"   Red team:")
    print(f"   - AP/AD ratio: {comp['red_ap_ad_ratio']:.2f}")
    print(f"   - Engage score: {comp['red_engage_score']:.2f}")
    print(f"   - CC score: {comp['red_cc_score']:.2f}")
    print(f"   - Poke score: {comp['red_poke_score']:.2f}")
    
    print("\n" + "="*70)
    print("✅ Feature Engineering Pipeline Test PASSED")
    print("="*70)


