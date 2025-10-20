"""
Utility helpers for building and comparing patch-level meta data.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Reuse the canonical ELO groupings used across the project
ELO_GROUPS = {
    "low": ["IRON", "BRONZE", "SILVER"],
    "mid": ["GOLD", "PLATINUM", "EMERALD"],
    "high": ["DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"],
}


def normalize_patch(patch: str) -> str:
    """Normalize patch strings to the canonical `major.minor[.micro]` format."""
    if not patch:
        raise ValueError("Patch must be a non-empty string")
    raw = patch.strip()
    raw = raw.replace("_", ".").replace("-", ".")
    parts = [p for p in raw.split(".") if p]
    # Keep up to 3 numeric segments
    normalized: List[str] = []
    for part in parts:
        if not part.isdigit():
            # Extract digits in case of strings like "15v20"
            digits = "".join(ch for ch in part if ch.isdigit())
            if not digits:
                continue
            normalized.append(str(int(digits)))
        else:
            normalized.append(str(int(part)))
        if len(normalized) == 3:
            break
    if not normalized:
        raise ValueError(f"Unable to normalize patch string: {patch}")
    return ".".join(normalized)


def _patch_sort_key(patch: str) -> Tuple[int, ...]:
    """Convert patch string into a sortable tuple."""
    segments = normalize_patch(patch).split(".")
    return tuple(int(seg) for seg in segments)


def get_latest_patch_from_api() -> Optional[str]:
    """
    Best-effort retrieval of the most recent patch.

    Attempts to read config/meta.json, falling back to the newest on-disk meta snapshot.
    """
    meta_path = Path("config/meta.json")
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            patch = data.get("patch")
            if patch:
                return normalize_patch(patch)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(f"Failed reading config/meta.json: {exc}")

    meta_dir = Path("data/meta")
    if meta_dir.exists():
        patches: List[Tuple[Tuple[int, ...], str]] = []
        for path in meta_dir.glob("*/*.json"):
            patch_name = path.stem
            try:
                patches.append((_patch_sort_key(patch_name), normalize_patch(patch_name)))
            except Exception:
                continue
        if patches:
            patches.sort(reverse=True)
            return patches[0][1]

    data_dir = Path("data/processed")
    if data_dir.exists():
        match_patches: List[Tuple[Tuple[int, ...], str]] = []
        for match_file in data_dir.glob("matches_*.json"):
            try:
                with open(match_file, "r", encoding="utf-8") as handle:
                    matches = json.load(handle)
            except Exception:
                continue
            for match in matches:
                patch = match.get("patch")
                if not patch:
                    continue
                try:
                    normalized = normalize_patch(patch)
                except ValueError:
                    continue
                match_patches.append((_patch_sort_key(normalized), normalized))
                break  # one patch per file is sufficient
        if match_patches:
            match_patches.sort(reverse=True)
            return match_patches[0][1]

    return None


def load_last_patch_meta(elo: str, exclude_patch: Optional[str] = None) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Load the most recent meta snapshot for an ELO, optionally excluding a patch.
    """
    elo_key = elo.lower()
    meta_dir = Path("data/meta") / elo_key
    if not meta_dir.exists():
        return None, None

    candidates: List[Tuple[Tuple[int, ...], Path]] = []
    for file_path in meta_dir.glob("*.json"):
        patch_name = file_path.stem
        try:
            patch_norm = normalize_patch(patch_name)
        except ValueError:
            continue
        if exclude_patch and normalize_patch(exclude_patch) == patch_norm:
            continue
        candidates.append((_patch_sort_key(patch_norm), file_path))

    if not candidates:
        return None, None

    candidates.sort(reverse=True)
    _, latest_path = candidates[0]

    try:
        with open(latest_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return normalize_patch(data.get("patch", latest_path.stem)), data
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"Failed loading meta snapshot {latest_path}: {exc}")
        return None, None


def compare_meta(
    current_meta: Dict,
    previous_meta: Optional[Dict]
) -> Dict[int, Dict[str, Optional[float]]]:
    """
    Compare two meta snapshots and compute delta win rates keyed by champion ID.
    """
    deltas: Dict[int, Dict[str, Optional[float]]] = {}
    prev_lookup: Dict[int, Dict] = {}

    if previous_meta:
        for entry in previous_meta.get("champions", []):
            try:
                prev_lookup[int(entry["champion_id"])] = entry
            except (KeyError, TypeError, ValueError):
                continue

    for entry in current_meta.get("champions", []):
        try:
            champ_id = int(entry["champion_id"])
        except (KeyError, TypeError, ValueError):
            continue
        prev_entry = prev_lookup.get(champ_id)
        prev_wr = prev_entry.get("win_rate") if prev_entry else None
        curr_wr = entry.get("win_rate")
        delta = None
        if isinstance(curr_wr, (int, float)) and isinstance(prev_wr, (int, float)):
            delta = curr_wr - prev_wr
        deltas[champ_id] = {
            "previous_win_rate": prev_wr,
            "delta_win_rate": delta,
        }
    return deltas


def available_patches(elo: str) -> List[str]:
    """Return all stored patches for an ELO sorted newest → oldest."""
    meta_dir = Path("data/meta") / elo.lower()
    if not meta_dir.exists():
        return []
    patches: List[Tuple[Tuple[int, ...], str]] = []
    for file_path in meta_dir.glob("*.json"):
        try:
            normalized = normalize_patch(file_path.stem)
            patches.append((_patch_sort_key(normalized), normalized))
        except ValueError:
            continue
    patches.sort(reverse=True)
    return [p[1] for p in patches]


__all__ = [
    "ELO_GROUPS",
    "normalize_patch",
    "get_latest_patch_from_api",
    "load_last_patch_meta",
    "compare_meta",
    "available_patches",
]
