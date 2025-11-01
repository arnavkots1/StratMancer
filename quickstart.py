"""
Quick start script to test the data collector.
Collects a small sample of matches for testing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.config_manager import get_config
from src.collectors.match_collector import MatchCollector
from src.utils.logging_config import setup_logging

def main():
    """Quick start: collect 10 matches from Gold rank"""
    print("=" * 60)
    print("StratMancer Quick Start Test")
    print("=" * 60)
    print()
    
    # Setup logging
    setup_logging(level="INFO")
    
    try:
        # Get configuration
        print("1. Loading configuration...")
        config = get_config()
        api_key = config.get_riot_api_key()
        print("   ✅ API key configured")
        
        # Initialize collector
        print("\n2. Initializing collector...")
        collector = MatchCollector(
            api_key=api_key,
            region='na1',
            save_raw=False
        )
        print(f"   ✅ Collector initialized (patch {collector.current_patch})")
        
        # Collect sample matches
        print("\n3. Collecting 10 sample matches from GOLD rank...")
        print("   (This may take 1-2 minutes)")
        match_count = collector.collect_for_rank('GOLD', target_matches=10)
        
        if match_count > 0:
            print(f"\n   ✅ Collected {match_count} matches successfully!")
        else:
            print("\n   ⚠️ No matches collected. Checking storage...")
            stats = collector.storage.get_statistics()
            if stats['total_matches'] > 0:
                print(f"   ✅ Found {stats['total_matches']} matches in storage")
        
        # Show statistics
        print("\n4. Data statistics:")
        stats = collector.storage.get_statistics()
        print(f"   Total matches: {stats['total_matches']}")
        if stats['by_rank']:
            print("   Matches by rank:")
            for rank, count in stats['by_rank'].items():
                print(f"     - {rank}: {count}")
        
        print("\n" + "=" * 60)
        print("Quick start test completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run full collection: python run_collector.py --ranks GOLD PLATINUM --matches-per-rank 100")
        print("2. Validate data: jupyter notebook notebooks/validation.ipynb")
        print("3. Read setup guide: SETUP_GUIDE.md")
        
        return 0
        
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease configure your Riot API key:")
        print("1. Copy .env.example to .env")
        print("2. Edit .env and add your API key")
        print("3. Run this script again")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

