"""
Synergy feature helpers for StratMancer rich feature pipeline.

Provides deterministic one-hot encodings for key friendly duos as well as
light-weight numeric cross-lane hooks that downstream models can learn from.
"""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np

# Role identifiers expected in draft payloads
ROLES = ["top", "jgl", "mid", "adc", "sup"]

FRIENDLY_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("top", "jgl"),
    ("mid", "jgl"),
    ("adc", "sup"),
)

# Cross-lane pairings where we want numeric interaction scores
CROSS_MATCHUPS: Tuple[Tuple[str, str], ...] = (
    ("top", "top"),
    ("mid", "mid"),
    ("jgl", "jgl"),
)


def _champ_index(champion_id: int, id_to_index: Dict[str, int]) -> int | None:
    """Lookup helper that tolerates missing champions."""
    if champion_id is None or champion_id < 0:
        return None
    key = str(champion_id)
    return id_to_index.get(key)


def build_duo_onehots(
    blue_ids_by_role: Dict[str, int | None],
    red_ids_by_role: Dict[str, int | None],
    id_to_index: Dict[str, int],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Construct compact numeric vectors representing friendly duo pairings.
    
    Instead of massive one-hot encodings (159K features), we use compact
    numeric features that store champion indices directly.
    
    For each duo pair (TOP×JGL, MID×JGL, ADC×SUP):
      - Champion A index (0-162)
      - Champion B index (0-162)
      - Interaction flag (1.0 if both present, 0.0 otherwise)
    
    This reduces feature space from 159K to just 18 features (3 pairs × 2 teams × 3 values).
    """
    num_champs = max(id_to_index.values(), default=-1) + 1
    if num_champs <= 0:
        return np.zeros(0, dtype=np.float32), np.zeros(len(CROSS_MATCHUPS), dtype=np.float32)

    # Compact encoding: 3 pairs × 2 teams × 3 values = 18 features
    friendly_vec = np.zeros(len(FRIENDLY_PAIRS) * 2 * 3, dtype=np.float32)

    def _encode_pair_compact(team_idx: int, pair_idx: int, champ_a: int | None, champ_b: int | None) -> None:
        """Encode a duo pair as [champ_a_idx, champ_b_idx, interaction_flag]"""
        a_idx = _champ_index(champ_a, id_to_index)
        b_idx = _champ_index(champ_b, id_to_index)
        
        offset = (team_idx * len(FRIENDLY_PAIRS) + pair_idx) * 3
        
        if a_idx is not None and b_idx is not None:
            # Normalize indices to [0, 1] range for better ML performance
            friendly_vec[offset + 0] = float(a_idx) / num_champs
            friendly_vec[offset + 1] = float(b_idx) / num_champs
            friendly_vec[offset + 2] = 1.0  # Both champions present
        else:
            # Missing pair - encode as zeros
            friendly_vec[offset + 0] = 0.0
            friendly_vec[offset + 1] = 0.0
            friendly_vec[offset + 2] = 0.0

    # Populate friendly pair encodings (compact!)
    for idx, (role_a, role_b) in enumerate(FRIENDLY_PAIRS):
        _encode_pair_compact(0, idx, blue_ids_by_role.get(role_a), blue_ids_by_role.get(role_b))
        _encode_pair_compact(1, idx, red_ids_by_role.get(role_a), red_ids_by_role.get(role_b))

    # Cross matchups numeric indicators (mirrored delta scaled to [-1, 1])
    cross_vec = np.zeros(len(CROSS_MATCHUPS), dtype=np.float32)
    for idx, (role_blue, role_red) in enumerate(CROSS_MATCHUPS):
        blue_id = blue_ids_by_role.get(role_blue)
        red_id = red_ids_by_role.get(role_red)
        b_idx = _champ_index(blue_id, id_to_index)
        r_idx = _champ_index(red_id, id_to_index)
        if b_idx is None or r_idx is None:
            cross_vec[idx] = 0.0
            continue
        # Deterministic numeric encoding using normalized index difference
        diff = float(b_idx - r_idx)
        cross_vec[idx] = diff / max(1.0, num_champs)

    return friendly_vec.astype(np.float32), cross_vec.astype(np.float32)


__all__ = ["build_duo_onehots", "ROLES", "FRIENDLY_PAIRS", "CROSS_MATCHUPS"]

