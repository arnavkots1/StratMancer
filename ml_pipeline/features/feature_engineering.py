"""
Feature engineering pipeline for draft prediction.
Converts match JSON/Parquet into fixed-length ML vectors.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

from ml_pipeline.meta_utils import normalize_patch

from .embeddings import load_embeddings
from .matchups import lane_advantage, load_matchup_matrices
from .synergy import CROSS_MATCHUPS, FRIENDLY_PAIRS, ROLES as SYNERGY_ROLES, build_duo_onehots


@dataclass
class FeatureFlags:
    """Toggles for optional rich feature components."""

    use_embeddings: bool = False
    use_matchups: bool = False
    use_synergy: bool = False
    ban_context: bool = False
    pick_order: bool = False


@dataclass
class FeatureContext:
    """Runtime context shared across feature assembly calls."""

    feature_map: Dict[str, Any]
    mode: str = "basic"
    elo_group: Optional[str] = None  # low / mid / high
    assets_dir: str = "data/assets"
    flags: FeatureFlags = field(default_factory=FeatureFlags)
    embedding_dim_hint: Optional[int] = None

    _priors_cache: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict, init=False)
    _matchup_cache: Dict[str, Dict[str, np.ndarray]] = field(default_factory=dict, init=False)
    _embeddings_matrix: Optional[np.ndarray] = field(default=None, init=False, repr=False)
    _attempted_embeddings: bool = field(default=False, init=False, repr=False)

    @property
    def id_to_index(self) -> Dict[str, int]:
        return self.feature_map.get("id_to_index", {})

    @property
    def num_champs(self) -> int:
        return int(self.feature_map["meta"]["num_champ"])

    @property
    def friendly_vector_length(self) -> int:
        pair_space = self.num_champs * self.num_champs
        return len(FRIENDLY_PAIRS) * 2 * pair_space

    @property
    def cross_vector_length(self) -> int:
        return len(CROSS_MATCHUPS)

    def get_priors(self, patch: str) -> Dict[str, Dict[str, float]]:
        if not self.elo_group:
            return {}
        patch_norm = normalize_patch(patch)
        if patch_norm in self._priors_cache:
            return self._priors_cache[patch_norm]
        path = Path(self.assets_dir) / f"priors_{self.elo_group}_{patch_norm}.json"
        if not path.exists():
            self._priors_cache[patch_norm] = {}
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            data = {}
        self._priors_cache[patch_norm] = data
        return data

    def get_matchups(self, patch: str) -> Dict[str, np.ndarray]:
        if not self.elo_group or not self.flags.use_matchups:
            return {}
        patch_norm = normalize_patch(patch)
        if patch_norm in self._matchup_cache:
            return self._matchup_cache[patch_norm]
        matrices = load_matchup_matrices(self.elo_group, patch_norm, self.assets_dir)
        self._matchup_cache[patch_norm] = matrices
        return matrices

    def get_embeddings(self) -> Optional[np.ndarray]:
        if self._attempted_embeddings:
            return self._embeddings_matrix
        self._attempted_embeddings = True
        if not self.flags.use_embeddings or not self.elo_group:
            self._embeddings_matrix = None
            return None
        matrix = load_embeddings(self.elo_group, self.assets_dir)
        self._embeddings_matrix = matrix
        return matrix

    @property
    def embedding_dim(self) -> int:
        matrix = self.get_embeddings()
        if matrix is not None:
            return int(matrix.shape[1])
        if self.embedding_dim_hint:
            return int(self.embedding_dim_hint)
        return 0


def _valid_ids(champion_ids: Iterable[int]) -> List[int]:
    return [cid for cid in champion_ids if cid is not None and cid >= 0]


def _team_prior_stats(
    champion_ids: Iterable[int],
    priors: Dict[str, Dict[str, float]],
) -> Tuple[float, float, float]:
    base_wr = []
    trend = []
    pick_rate = []
    for cid in champion_ids:
        entry = priors.get(str(cid))
        if not entry:
            continue
        base_wr.append(entry.get("base_wr", 0.5))
        trend.append(entry.get("trend_3patch", 0.0))
        pick_rate.append(entry.get("pick_rate", 0.0))
    if base_wr:
        return float(np.mean(base_wr)), float(np.mean(trend)), float(np.mean(pick_rate))
    return 0.5, 0.0, 0.0


def _recent_features(derived: Dict[str, Any]) -> np.ndarray:
    if not derived:
        return np.zeros(2, dtype=np.float32)
    blue_freq = derived.get("recent_play_freq_blue", derived.get("recent_play_freq", 0.0))
    red_freq = derived.get("recent_play_freq_red", derived.get("recent_play_freq_enemy", 0.0))
    if isinstance(blue_freq, dict):
        blue_freq = float(np.mean(list(blue_freq.values()))) if blue_freq else 0.0
    if isinstance(red_freq, dict):
        red_freq = float(np.mean(list(red_freq.values()))) if red_freq else 0.0
    delta_wr = derived.get("recent_wr_delta", 0.0)
    if isinstance(delta_wr, dict):
        delta_wr = float(np.mean(list(delta_wr.values()))) if delta_wr else 0.0
    return np.array([float(blue_freq), float(red_freq if red_freq else delta_wr)], dtype=np.float32)


def _compute_ban_context_features(
    blue_ids_by_role: Dict[str, Optional[int]],
    red_ids_by_role: Dict[str, Optional[int]],
    blue_bans: List[int],
    red_bans: List[int],
    priors: Dict[str, Dict[str, float]],
    matchup_matrices: Dict[str, np.ndarray],
    id_to_index: Dict[str, int],
) -> np.ndarray:
    if not priors:
        return np.zeros(4, dtype=np.float32)

    def candidate_scores(
        ally_roles: Dict[str, Optional[int]],
        enemy_roles: Dict[str, Optional[int]],
        our_bans: List[int],
        enemy_bans: List[int],
    ) -> Tuple[float, float]:
        excluded = set(_valid_ids(ally_roles.values()))
        excluded.update(_valid_ids(enemy_roles.values()))
        excluded.update(_valid_ids(our_bans))
        excluded.update(_valid_ids(enemy_bans))

        sorted_candidates = sorted(
            priors.items(),
            key=lambda kv: kv[1].get("pick_rate", 0.0),
            reverse=True,
        )

        top_k = []
        for champ_id_str, info in sorted_candidates:
            champ_id = int(champ_id_str)
            if champ_id in excluded:
                continue
            top_k.append((champ_id, info))
            if len(top_k) >= 3:
                break

        if not top_k:
            return 0.0, 0.0

        threat_scores = []
        comfort = []
        for champ_id, info in top_k:
            comfort.append(info.get("pick_rate", 0.0))
            threat = 0.0
            idx_enemy = id_to_index.get(str(champ_id))
            if idx_enemy is None:
                continue
            for role in SYNERGY_ROLES:
                matrix = matchup_matrices.get(role)
                ally_id = ally_roles.get(role)
                if matrix is None or ally_id is None or ally_id < 0:
                    continue
                ally_idx = id_to_index.get(str(ally_id))
                if ally_idx is None:
                    continue
                if ally_idx >= matrix.shape[0] or idx_enemy >= matrix.shape[1]:
                    continue
                score = -float(matrix[ally_idx, idx_enemy])
                threat = max(threat, score)
            threat_scores.append(threat)

        if not threat_scores:
            threat_scores = [0.0]
        if not comfort:
            comfort = [0.0]

        return float(np.mean(threat_scores)), float(np.mean(comfort))

    blue_threat, blue_comfort = candidate_scores(
        blue_ids_by_role, red_ids_by_role, blue_bans, red_bans
    )
    red_threat, red_comfort = candidate_scores(
        red_ids_by_role, blue_ids_by_role, red_bans, blue_bans
    )

    return np.array([blue_threat, red_threat, blue_comfort, red_comfort], dtype=np.float32)


ELO_GROUPS = {
    "low": ["IRON", "BRONZE", "SILVER"],
    "mid": ["GOLD", "PLATINUM", "EMERALD"],
    "high": ["DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"],
}
ELO_LOOKUP = {rank: group for group, ranks in ELO_GROUPS.items() for rank in ranks}


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
    
    # Check if this is a positional pick array (from API prediction)
    # If blue_picks is a list of exactly 5 elements, treat as positional
    if (isinstance(match.get('blue_picks'), list) and 
        len(match['blue_picks']) == 5 and
        isinstance(match.get('red_picks'), list) and 
        len(match['red_picks']) == 5):
        
        # Process as positional arrays: [top, jgl, mid, adc, sup]
        for team_idx, team_picks in enumerate([match['blue_picks'], match['red_picks']]):
            for role_idx, champ_id in enumerate(team_picks):
                if champ_id != -1:  # Skip empty positions
                    champ_str = str(champ_id)
                    if champ_str in id_to_index:
                        champ_idx = id_to_index[champ_str]
                        role_matrix[team_idx, role_idx, champ_idx] = 1.0
    else:
        # Legacy behavior: look up champion roles from feature map
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
    history_index: Optional[Any] = None,
    mode: str = "basic",
    context: Optional[FeatureContext] = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Assemble complete feature vector from match data.

    Optional ``FeatureContext`` allows toggling the richer feature pipeline
    while keeping backwards compatibility with the legacy basic vector.
    """
    if feature_map is None:
        feature_map = load_feature_map()

    if context is None:
        context = FeatureContext(feature_map=feature_map, mode=mode)
    else:
        if context.feature_map is not feature_map:
            context.feature_map = feature_map

    if not context.elo_group:
        elo_upper = elo.upper()
        context.elo_group = ELO_LOOKUP.get(elo_upper, context.elo_group)

    effective_mode = context.mode or mode

    # 1. Role-based one-hots (champion picks by role)
    role_onehots = build_role_onehots(match, feature_map)

    # 2. Ban one-hots
    ban_onehots = build_ban_onehots(match, feature_map)

    # 3. Composition shape features
    comp_features = comp_shape_features(match, feature_map)
    comp_vector = np.array(list(comp_features.values()), dtype=np.float32)

    # 4. Patch features
    patch_vector = patch_features(match.get("patch", "15.20"))

    # 5. ELO encoding (one-hot)
    elo_ranks = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM',
                 'EMERALD', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
    elo_onehot = np.zeros(len(elo_ranks), dtype=np.float32)
    if elo.upper() in elo_ranks:
        elo_onehot[elo_ranks.index(elo.upper())] = 1.0

    # 6. Historical features (synergy + counter)
    # NOTE: Only use history_index in basic mode. Rich mode uses fresh assets instead.
    if history_index is not None and effective_mode != "rich":
        try:
            synergy_blue = history_index.get_synergy(match['blue_picks'], elo)
            synergy_red = history_index.get_synergy(match['red_picks'], elo)
            counter_score = history_index.get_counter(
                match['blue_picks'],
                match['red_picks'],
                elo
            )
            history_vector = np.array([synergy_blue, synergy_red, counter_score], dtype=np.float32)
        except Exception:
            history_vector = np.zeros(3, dtype=np.float32)
    else:
        history_vector = np.zeros(3, dtype=np.float32)

    # 7. Objective features (if available in derived_features)
    derived = match.get('derived_features', {})
    objectives_vector = np.array([
        derived.get('ap_ad_ratio', comp_features.get('blue_ap_ad_ratio', 0.5)),
        derived.get('engage_score', comp_features.get('blue_engage_score', 0.5)),
        derived.get('splitpush_score', comp_features.get('blue_splitpush_score', 0.5)),
        derived.get('teamfight_synergy', 0.5)
    ], dtype=np.float32)

    segments: List[np.ndarray] = [
        role_onehots,
        ban_onehots,
        comp_vector,
        patch_vector,
        elo_onehot,
        history_vector,
        objectives_vector,
    ]

    patch_str = match.get("patch", feature_map["meta"].get("patch", "15.20"))
    patch_norm = normalize_patch(patch_str)

    blue_picks = match.get("blue_picks", [])
    red_picks = match.get("red_picks", [])

    blue_ids_by_role = {
        role: (blue_picks[idx] if idx < len(blue_picks) and blue_picks[idx] not in (None, -1) else None)
        for idx, role in enumerate(SYNERGY_ROLES)
    }
    red_ids_by_role = {
        role: (red_picks[idx] if idx < len(red_picks) and red_picks[idx] not in (None, -1) else None)
        for idx, role in enumerate(SYNERGY_ROLES)
    }

    if effective_mode == "rich":
        id_to_index = context.id_to_index

        if context.flags.use_synergy:
            friendly_vec, cross_vec = build_duo_onehots(blue_ids_by_role, red_ids_by_role, id_to_index)
            segments.extend([friendly_vec, cross_vec])

        priors_lookup = context.get_priors(patch_norm) if (context.flags.use_synergy or context.flags.ban_context) else {}
        matchup_matrices = context.get_matchups(patch_norm) if context.flags.use_matchups else {}

        if matchup_matrices:
            lane_scores = lane_advantage(blue_ids_by_role, red_ids_by_role, matchup_matrices, id_to_index)
            lane_vector = np.array(
                [lane_scores.get(f"{role}_adv", 0.0) for role in SYNERGY_ROLES] +
                [lane_scores.get("lane_counter_score", 0.0)],
                dtype=np.float32,
            )
            segments.append(lane_vector)

        if priors_lookup:
            blue_prior_wr, blue_trend, blue_pickrate = _team_prior_stats(_valid_ids(blue_picks), priors_lookup)
            red_prior_wr, red_trend, red_pickrate = _team_prior_stats(_valid_ids(red_picks), priors_lookup)
            priors_vector = np.array([blue_prior_wr, red_prior_wr, blue_trend, red_trend], dtype=np.float32)
            segments.append(priors_vector)
        else:
            blue_pickrate = red_pickrate = 0.0

        if context.flags.use_embeddings:
            embeddings = context.get_embeddings()
            emb_dim = context.embedding_dim
            if emb_dim > 0:
                blue_emb = np.zeros(emb_dim, dtype=np.float32)
                red_emb = np.zeros(emb_dim, dtype=np.float32)
                if embeddings is not None:
                    for champ_id in _valid_ids(blue_picks):
                        idx = id_to_index.get(str(champ_id))
                        if idx is None or idx >= embeddings.shape[0]:
                            continue
                        blue_emb += embeddings[idx]
                    for champ_id in _valid_ids(red_picks):
                        idx = id_to_index.get(str(champ_id))
                        if idx is None or idx >= embeddings.shape[0]:
                            continue
                        red_emb += embeddings[idx]
                segments.extend([blue_emb, red_emb])

        if context.flags.ban_context:
            ban_vector = _compute_ban_context_features(
                blue_ids_by_role,
                red_ids_by_role,
                match.get("blue_bans", []),
                match.get("red_bans", []),
                priors_lookup,
                matchup_matrices,
                id_to_index,
            )
            segments.append(ban_vector)

        recent_vector = _recent_features(derived)
        segments.append(recent_vector)

        if context.flags.pick_order:
            draft_info = match.get("draft_context", match.get("draft_meta", {}))
            pick_vector = np.zeros(5, dtype=np.float32)
            step_index = draft_info.get("step_index")
            if isinstance(step_index, int):
                pick_vector[0] = 1.0 if step_index < 6 else 0.0
                pick_vector[1] = 1.0 if 6 <= step_index < 10 else 0.0
                pick_vector[2] = 1.0 if 10 <= step_index < 14 else 0.0
            phase = draft_info.get("phase")
            if isinstance(phase, str) and "ban" in phase.lower():
                pick_vector[3] = 1.0
            remaining_roles = draft_info.get("remaining_roles")
            if isinstance(remaining_roles, int):
                pick_vector[4] = float(remaining_roles)
            segments.append(pick_vector)

    # DEBUG: Log each segment size to find the culprit
    segment_sizes = []
    segment_names = ['role_onehots', 'ban_onehots', 'comp_vector', 'patch_vector', 
                     'elo_onehot', 'history_vector', 'objectives_vector']
    
    for i, seg in enumerate(segments):
        size = len(seg)
        name = segment_names[i] if i < len(segment_names) else f'segment_{i}'
        segment_sizes.append((name, size))
        if size > 10000:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️  LARGE SEGMENT FOUND: {name} has {size} features!")
    
    X_vec = np.concatenate([seg.astype(np.float32, copy=False) for seg in segments])
    X_vec = np.nan_to_num(X_vec, nan=0.0, posinf=0.0, neginf=0.0)

    named = {
        'match_id': match.get('match_id', 'unknown'),
        'patch': match.get('patch', 'unknown'),
        'patch_normalized': patch_norm,
        'elo': elo,
        'mode': effective_mode,
        'flags': context.flags.__dict__,
        'blue_picks': match['blue_picks'],
        'red_picks': match['red_picks'],
        'blue_win': match.get('blue_win', None),
        'n_role_features': len(role_onehots),
        'n_ban_features': len(ban_onehots),
        'n_comp_features': len(comp_vector),
        'comp_features': comp_features,
        'total_features': len(X_vec),
        'segment_breakdown': segment_sizes  # Add this for debugging
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


