"""
Feature engineering pipeline for StratMancer ML models.
Converts match data into fixed-length ML-ready vectors.
"""

from .feature_engineering import (
    load_feature_map,
    build_role_onehots,
    build_ban_onehots,
    comp_shape_features,
    patch_features,
    assemble_features,
    FeatureContext,
    FeatureFlags,
)

from .history_index import (
    HistoryIndex,
    get_synergy,
    get_counter,
)

from .synergy import build_duo_onehots
from .matchups import load_matchup_matrices, lane_advantage
from .embeddings import load_embeddings

__all__ = [
    "load_feature_map",
    "build_role_onehots",
    "build_ban_onehots",
    "comp_shape_features",
    "patch_features",
    "assemble_features",
    "FeatureContext",
    "FeatureFlags",
    "HistoryIndex",
    "get_synergy",
    "get_counter",
    "build_duo_onehots",
    "load_matchup_matrices",
    "lane_advantage",
    "load_embeddings",
]
