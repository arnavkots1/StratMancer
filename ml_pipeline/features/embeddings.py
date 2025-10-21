"""
Champion embedding helpers loaded from asset files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import numpy as np

EMBEDDING_CACHE: Dict[Tuple[str, str], np.ndarray] = {}


def load_embeddings(
    elo_group: str,
    assets_dir: str = "data/assets",
) -> np.ndarray | None:
    """
    Load co-pick/ban embeddings for a given elo group.

    Returns ``None`` when the asset is unavailable.
    """
    key = (elo_group.lower(), assets_dir)
    if key in EMBEDDING_CACHE:
        return EMBEDDING_CACHE[key]

    path = Path(assets_dir) / f"embeddings_{elo_group.lower()}.npy"
    if not path.exists():
        EMBEDDING_CACHE[key] = None
        return None

    embeddings = np.load(path)
    EMBEDDING_CACHE[key] = embeddings
    return embeddings


__all__ = ["load_embeddings"]

