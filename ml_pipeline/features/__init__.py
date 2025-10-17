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
    assemble_features
)

from .history_index import (
    HistoryIndex,
    get_synergy,
    get_counter
)

__all__ = [
    'load_feature_map',
    'build_role_onehots',
    'build_ban_onehots',
    'comp_shape_features',
    'patch_features',
    'assemble_features',
    'HistoryIndex',
    'get_synergy',
    'get_counter'
]
