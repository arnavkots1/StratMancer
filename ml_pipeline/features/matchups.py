"""
Lane matchup helpers backed by pre-computed assets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

from .synergy import ROLES

MATCHUP_CACHE: Dict[Tuple[str, str], Dict[str, np.ndarray]] = {}


def load_matchup_matrices(
    elo_group: str,
    patch: str,
    assets_dir: str = "data/assets",
) -> Dict[str, np.ndarray]:
    """
    Load per-role matchup matrices for an elo/patch combination.

    Each matrix is shaped [N_champ, N_champ] and stores a win-rate delta
    in [-0.2, 0.2] from the perspective of the row champion versus the
    column champion.
    """
    key = (elo_group.lower(), patch)
    if key in MATCHUP_CACHE:
        return MATCHUP_CACHE[key]

    path = Path(assets_dir) / f"matchups_{elo_group.lower()}_{patch}.npz"
    if not path.exists():
        MATCHUP_CACHE[key] = {}
        return {}

    data = np.load(path)
    matrices: Dict[str, np.ndarray] = {}
    for role in data.files:
        matrices[role] = data[role]

    MATCHUP_CACHE[key] = matrices
    return matrices


def lane_advantage(
    blue_ids_by_role: Dict[str, int | None],
    red_ids_by_role: Dict[str, int | None],
    matrices: Dict[str, np.ndarray],
    id_to_index: Dict[str, int],
) -> Dict[str, float]:
    """
    Compute lane advantages for each role given matchup matrices.

    Returns a dictionary containing per-role deltas (positive favours blue)
    as well as a combined ``lane_counter_score``.
    """
    results: Dict[str, float] = {}
    total = 0.0
    count = 0

    for role in ROLES:
        matrix = matrices.get(role)
        if matrix is None:
            results[f"{role}_adv"] = 0.0
            continue

        blue_id = blue_ids_by_role.get(role)
        red_id = red_ids_by_role.get(role)

        if blue_id is None or red_id is None or blue_id < 0 or red_id < 0:
            results[f"{role}_adv"] = 0.0
            continue

        b_idx = id_to_index.get(str(blue_id))
        r_idx = id_to_index.get(str(red_id))
        if b_idx is None or r_idx is None:
            results[f"{role}_adv"] = 0.0
            continue

        if b_idx >= matrix.shape[0] or r_idx >= matrix.shape[1]:
            results[f"{role}_adv"] = 0.0
            continue

        value = float(matrix[b_idx, r_idx])
        results[f"{role}_adv"] = value
        total += value
        count += 1

    results["lane_counter_score"] = total if count == 0 else total / count
    return results


__all__ = ["load_matchup_matrices", "lane_advantage"]

