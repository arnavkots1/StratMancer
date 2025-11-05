"""
Rebuild feature map to ensure all features are included.
This fixes feature count mismatches and ensures the feature map is up to date.
"""
import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, '.')

from ml_pipeline.features.tag_builder import ChampionTagBuilder

async def rebuild_feature_map(
    data_dir: str = "./data",
    output_path: str = "./ml_pipeline/feature_map.json",
    overrides_path: str = "./ml_pipeline/tags_overrides.yaml"
):
    """
    Rebuild the feature map from champion data and API.
    
    Args:
        data_dir: Directory containing match data
        output_path: Path to save feature map JSON
        overrides_path: Path to champion tag overrides YAML
    """
    print("=" * 70)
    print("Rebuilding Feature Map")
    print("=" * 70)
    print(f"Data directory: {data_dir}")
    print(f"Output path: {output_path}")
    print(f"Overrides: {overrides_path}")
    print("=" * 70)
    
    # Create builder
    builder = ChampionTagBuilder(
        data_dir=data_dir,
        overrides_path=overrides_path
    )
    
    # Build tags
    print("\nBuilding champion tags from API and local data...")
    feature_map = await builder.build_tags()
    
    # Save output
    builder.save_feature_map(output_path, feature_map)
    
    # Print summary
    print("\n" + "=" * 70)
    print("Feature Map Rebuild Complete!")
    print("=" * 70)
    print(f"Total champions: {feature_map['meta']['num_champ']}")
    print(f"Current patch: {feature_map['meta']['patch']}")
    print(f"Overrides applied: {feature_map['meta']['overrides_applied']}")
    print(f"\nExpected feature vector length:")
    
    # Calculate expected feature count
    num_champs = feature_map['meta']['num_champ']
    role_features = 2 * 5 * num_champs  # 2 teams × 5 roles × champs
    ban_features = 2 * 5 * num_champs   # 2 teams × 5 bans × champs
    comp_features = 30                   # Composition metrics
    patch_features = 2                    # Patch encoding
    elo_features = 10                    # ELO one-hot
    history_features = 3                  # Synergy + counter
    total_expected = role_features + ban_features + comp_features + patch_features + elo_features + history_features
    
    print(f"  Role one-hots: {role_features}")
    print(f"  Ban one-hots: {ban_features}")
    print(f"  Composition: {comp_features}")
    print(f"  Patch: {patch_features}")
    print(f"  ELO: {elo_features}")
    print(f"  History: {history_features}")
    print(f"  TOTAL: {total_expected}")
    print(f"\nOutput saved to: {output_path}")
    print("=" * 70)
    
    return feature_map


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rebuild feature map from champion data and API"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Directory containing match data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./ml_pipeline/feature_map.json",
        help="Output path for feature map JSON"
    )
    parser.add_argument(
        "--overrides",
        type=str,
        default="./ml_pipeline/tags_overrides.yaml",
        help="Path to champion tag overrides YAML file"
    )
    
    args = parser.parse_args()
    
    try:
        feature_map = asyncio.run(rebuild_feature_map(
            data_dir=args.data_dir,
            output_path=args.output,
            overrides_path=args.overrides
        ))
        print("\n✅ Feature map rebuilt successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error rebuilding feature map: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

