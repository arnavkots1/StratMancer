"""Verify the fix is working - fresh test"""
import sys
import importlib

# Force fresh imports by clearing cache
if 'ml_pipeline' in sys.modules:
    del sys.modules['ml_pipeline']
if 'ml_pipeline.features' in sys.modules:
    del sys.modules['ml_pipeline.features']
if 'ml_pipeline.features.feature_engineering' in sys.modules:
    del sys.modules['ml_pipeline.features.feature_engineering']

sys.path.insert(0, '.')

from ml_pipeline.features import load_feature_map, assemble_features, FeatureContext, FeatureFlags
from pathlib import Path
import json

# Load one match
match_file = Path("data/processed/matches_GOLD.json")
with open(match_file, 'r') as f:
    matches = json.load(f)

match = matches[0]
feature_map = load_feature_map()

# Test rich mode WITHOUT history_index
flags = FeatureFlags(
    use_embeddings=True,
    use_matchups=True,
    use_synergy=True,
    ban_context=True,
    pick_order=False,
)

context = FeatureContext(
    feature_map=feature_map,
    mode="rich",
    flags=flags,
    elo_group="mid",
    assets_dir="data/assets",
)

# CRITICAL: Pass history_index=None explicitly
X_vec, named = assemble_features(
    match,
    "GOLD",
    feature_map,
    history_index=None,  # ← Should be None for rich mode
    mode="rich",
    context=context,
)

print(f"\n{'='*60}")
print(f"Feature Shape Test for Rich Mode")
print(f"{'='*60}")
print(f"✅ Feature vector shape: {X_vec.shape}")
print(f"✅ Total features: {X_vec.shape[0]}")
print(f"\nFeature Breakdown:")
print(f"  - Role onehots: {named['n_role_features']}")
print(f"  - Ban onehots: {named['n_ban_features']}")
print(f"  - Comp features: {named['n_comp_features']}")
print(f"  - Total: {named['total_features']}")

print(f"\nDetailed Segment Sizes:")
for name, size in named.get('segment_breakdown', []):
    status = "❌ HUGE!" if size > 10000 else "⚠️ Large" if size > 1000 else "✅"
    print(f"  {status} {name}: {size} features")

if X_vec.shape[0] > 10000:
    print(f"\n❌ FAILED: Still have {X_vec.shape[0]} features (should be ~487)")
    print("   The history_index is still being loaded somewhere!")
elif X_vec.shape[0] < 1000:
    print(f"\n✅ SUCCESS: Feature count is correct!")
    print("   Training will now work properly.")
else:
    print(f"\n❓ UNEXPECTED: {X_vec.shape[0]} features (expected ~487)")

