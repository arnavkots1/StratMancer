"""
Asset builder for StratMancer rich feature pipeline.
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

from ml_pipeline.features import load_feature_map
from ml_pipeline.meta_utils import (
    ELO_GROUPS,
    normalize_patch,
    load_last_patch_meta,
    available_patches,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ROLES = ["top", "jgl", "mid", "adc", "sup"]


def load_matches_for_group(elo_group: str, data_dir: Path) -> List[dict]:
    matches: List[dict] = []
    for elo in ELO_GROUPS[elo_group]:
        path = data_dir / f"matches_{elo}.json"
        if not path.exists():
            logger.warning("No data for %s at %s", elo, path)
            continue
        with open(path, "r", encoding="utf-8") as handle:
            matches.extend(json.load(handle))
    return matches


def role_dict(picks: Iterable[int]) -> Dict[str, int | None]:
    mapping: Dict[str, int | None] = {}
    for role, champ_id in zip(ROLES, picks):
        mapping[role] = champ_id if champ_id is not None else -1
    return mapping


def build_matchup_assets(
    matches: Iterable[dict],
    id_to_index: Dict[str, int],
    num_champs: int,
    smoothing: float = 5.0,
) -> Dict[str, np.ndarray]:
    wins = {role: np.zeros((num_champs, num_champs), dtype=np.float64) for role in ROLES}
    totals = {role: np.zeros((num_champs, num_champs), dtype=np.float64) for role in ROLES}

    for match in matches:
        blue = role_dict(match["blue_picks"])
        red = role_dict(match["red_picks"])
        blue_win = bool(match.get("blue_win"))

        for idx, role in enumerate(ROLES):
            blue_id = blue[role]
            red_id = red[role]
            if blue_id is None or red_id is None or blue_id < 0 or red_id < 0:
                continue

            b_idx = id_to_index.get(str(blue_id))
            r_idx = id_to_index.get(str(red_id))
            if b_idx is None or r_idx is None:
                continue

            totals[role][b_idx, r_idx] += 1.0
            totals[role][r_idx, b_idx] += 1.0
            if blue_win:
                wins[role][b_idx, r_idx] += 1.0
            else:
                wins[role][r_idx, b_idx] += 1.0

    matrices: Dict[str, np.ndarray] = {}
    for role in ROLES:
        numerator = wins[role] + smoothing * 0.5
        denominator = totals[role] + smoothing
        winrate = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
        delta = np.clip(winrate - 0.5, -0.2, 0.2)
        matrices[role] = delta.astype(np.float32)

    return matrices


def build_priors(
    matches: Iterable[dict],
    id_to_index: Dict[str, int],
    num_champs: int,
    elo_group: str,
    patch: str,
    meta_dir: Path,
) -> Dict[str, Dict[str, float]]:
    pick_counts = np.zeros(num_champs, dtype=np.float64)
    win_counts = np.zeros(num_champs, dtype=np.float64)

    total_matches = 0
    for match in matches:
        total_matches += 1
        blue_picks = match["blue_picks"]
        red_picks = match["red_picks"]
        blue_win = bool(match.get("blue_win"))

        for champ_id in blue_picks:
            idx = id_to_index.get(str(champ_id))
            if idx is None:
                continue
            pick_counts[idx] += 1
            if blue_win:
                win_counts[idx] += 1

        for champ_id in red_picks:
            idx = id_to_index.get(str(champ_id))
            if idx is None:
                continue
            pick_counts[idx] += 1
            if not blue_win:
                win_counts[idx] += 1

    with np.errstate(divide="ignore", invalid="ignore"):
        base_wr = np.divide(win_counts, pick_counts, out=np.zeros_like(win_counts), where=pick_counts > 0)

    total_picks = max(total_matches * 10, 1)
    pick_rate = pick_counts / total_picks

    trend = compute_trend_three_patch(elo_group, patch, meta_dir, id_to_index)

    priors: Dict[str, Dict[str, float]] = {}
    for champ_id, idx in id_to_index.items():
        priors[champ_id] = {
            "base_wr": float(base_wr[idx]),
            "pick_rate": float(pick_rate[idx]),
            "trend_3patch": float(trend.get(idx, 0.0)),
        }
    return priors


def compute_trend_three_patch(
    elo_group: str,
    patch: str,
    meta_dir: Path,
    id_to_index: Dict[str, int],
) -> Dict[int, float]:
    """Compute simple delta between current patch WR and mean of previous two patches."""
    elo_dir = meta_dir / elo_group.lower()
    if not elo_dir.exists():
        return {}

    current_meta_path = elo_dir / f"{patch}.json"
    if not current_meta_path.exists():
        return {}

    with open(current_meta_path, "r", encoding="utf-8") as handle:
        current_meta = json.load(handle)

    prev_candidates = available_patches(elo_group)
    patch_key = tuple(int(part) for part in patch.split("."))
    filtered_prev = []
    for prev in prev_candidates:
        prev_key = tuple(int(part) for part in prev.split("."))
        if prev_key < patch_key:
            filtered_prev.append(prev)
    prev_patches = filtered_prev[:2]

    prev_wr_lookup: Dict[int, List[float]] = defaultdict(list)

    for prev_patch in prev_patches:
        prev_path = elo_dir / f"{prev_patch}.json"
        if not prev_path.exists():
            continue
        with open(prev_path, "r", encoding="utf-8") as handle:
            prev_meta = json.load(handle)
        for entry in prev_meta.get("champions", []):
            champ_id = int(entry["champion_id"])
            prev_wr_lookup[champ_id].append(float(entry.get("win_rate", 0.5)))

    trend: Dict[int, float] = {}
    curr_wr_lookup = {int(entry["champion_id"]): float(entry.get("win_rate", 0.5)) for entry in current_meta.get("champions", [])}
    for champ_id, curr_wr in curr_wr_lookup.items():
        prev_wr_values = prev_wr_lookup.get(champ_id)
        idx = id_to_index.get(str(champ_id))
        if idx is None:
            continue
        if prev_wr_values:
            trend[idx] = curr_wr - float(np.mean(prev_wr_values))
        else:
            trend[idx] = 0.0
    return trend


def build_embeddings(
    matches: Iterable[dict],
    id_to_index: Dict[str, int],
    num_champs: int,
    embedding_dim: int,
    laplace_k: float = 5.0,
) -> np.ndarray:
    matrix = np.zeros((num_champs, num_champs), dtype=np.float64)

    for match in matches:
        for team in ("blue_picks", "red_picks"):
            champs = [id_to_index.get(str(cid)) for cid in match[team] if id_to_index.get(str(cid)) is not None]
            for i in champs:
                matrix[i, i] += 1.0
            for i in champs:
                for j in champs:
                    if i == j:
                        continue
                    matrix[i, j] += 1.0

        for bans in ("blue_bans", "red_bans"):
            champs = [id_to_index.get(str(cid)) for cid in match[bans][:5] if id_to_index.get(str(cid)) is not None]
            for i in champs:
                matrix[i, i] += 0.5
            for i in champs:
                for j in champs:
                    if i == j:
                        continue
                    matrix[i, j] += 0.5

    # Symmetrise and smooth
    matrix = (matrix + matrix.T) / 2.0
    matrix += laplace_k * np.eye(num_champs)

    # SVD factorisation
    try:
        u, s, _ = np.linalg.svd(matrix, full_matrices=False)
    except Exception:
        logger.exception("SVD failed; falling back to eigendecomposition")
        s, u = np.linalg.eigh(matrix)
        idx = np.argsort(s)[::-1]
        s = s[idx]
        u = u[:, idx]

    dim = min(embedding_dim, u.shape[1])
    embeddings = u[:, :dim] * np.sqrt(s[:dim])
    return embeddings.astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build rich feature assets.")
    parser.add_argument("--elo", required=True, choices=list(ELO_GROUPS.keys()), help="ELO group to build assets for")
    parser.add_argument("--patch", required=True, help="Target patch (e.g. 14.21)")
    parser.add_argument("--embedding-dim", type=int, default=32, help="Embedding dimensionality")
    parser.add_argument("--min-samples", type=int, default=200, help="Minimum matches required (unused but logged)")
    parser.add_argument("--data-dir", default="data/processed", help="Directory with processed match files")
    parser.add_argument("--meta-dir", default="data/meta", help="Directory with meta snapshots")
    parser.add_argument("--assets-dir", default="data/assets", help="Output asset directory")
    args = parser.parse_args()

    elo_group = args.elo.lower()
    target_patch = normalize_patch(args.patch)
    data_dir = Path(args.data_dir)
    assets_dir = Path(args.assets_dir)
    meta_dir = Path(args.meta_dir)

    feature_map = load_feature_map()
    id_to_index = feature_map.get("id_to_index", {})
    num_champs = feature_map["meta"]["num_champ"]

    matches_all = load_matches_for_group(elo_group, data_dir)
    if not matches_all:
        logger.error("No matches found for %s in %s", elo_group, data_dir)
        return

    matches = [
        m for m in matches_all if normalize_patch(m.get("patch", target_patch)) == target_patch
    ]

    if not matches:
        logger.warning("No matches aligned with patch %s; using all available matches.", target_patch)
        matches = matches_all

    logger.info("Using %d matches for elo=%s patch=%s", len(matches), elo_group, target_patch)

    assets_dir.mkdir(parents=True, exist_ok=True)

    matchup_matrices = build_matchup_assets(matches, id_to_index, num_champs)
    matchup_path = assets_dir / f"matchups_{elo_group}_{target_patch}.npz"
    np.savez_compressed(matchup_path, **matchup_matrices)
    logger.info("Saved matchup matrices to %s", matchup_path)

    priors = build_priors(matches, id_to_index, num_champs, elo_group, target_patch, meta_dir)
    priors_path = assets_dir / f"priors_{elo_group}_{target_patch}.json"
    with open(priors_path, "w", encoding="utf-8") as handle:
        json.dump(priors, handle, indent=2)
    logger.info("Saved priors to %s", priors_path)

    embeddings = build_embeddings(matches, id_to_index, num_champs, args.embedding_dim)
    embeddings_path = assets_dir / f"embeddings_{elo_group}.npy"
    np.save(embeddings_path, embeddings)
    logger.info("Saved embeddings to %s (shape=%s)", embeddings_path, embeddings.shape)

    avg_lane_samples = {
        role: float(np.count_nonzero(matchup_matrices[role])) for role in ROLES
    }
    logger.info("Coverage stats: avg lane coverage %s", avg_lane_samples)
    logger.info("Asset build complete.")


if __name__ == "__main__":
    main()
