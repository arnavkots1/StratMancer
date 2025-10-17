"""
Status checker - verify project setup and data collection progress.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_dependencies():
    """Check if all required packages are installed"""
    print("Checking dependencies...")
    required = ['requests', 'pandas', 'pyarrow', 'pydantic', 'yaml', 'tqdm']
    missing = []
    
    for package in required:
        try:
            if package == 'yaml':
                __import__('yaml')
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing.append(package)
    
    return len(missing) == 0

def check_config():
    """Check if configuration is set up"""
    print("\nChecking configuration...")
    
    try:
        from src.utils.config_manager import get_config
        config = get_config()
        
        # Check API key
        try:
            api_key = config.get_riot_api_key()
            if api_key and api_key != 'RGAPI-YOUR-API-KEY-HERE':
                print("  ✅ API key configured")
                return True
            else:
                print("  ❌ API key not configured")
                print("     → Set RIOT_API_KEY in .env or config/config.yaml")
                return False
        except ValueError:
            print("  ❌ API key not configured")
            print("     → Set RIOT_API_KEY in .env or config/config.yaml")
            return False
            
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

def check_data():
    """Check collected data"""
    print("\nChecking collected data...")
    
    try:
        from src.storage.data_storage import DataStorage
        storage = DataStorage(base_path='data')
        
        stats = storage.get_statistics()
        total = stats['total_matches']
        
        if total > 0:
            print(f"  ✅ {total} matches collected")
            print("\n  Breakdown by rank:")
            for rank, count in sorted(stats['by_rank'].items()):
                print(f"    - {rank}: {count}")
            
            if stats['by_patch']:
                print("\n  Breakdown by patch:")
                for patch, count in sorted(stats['by_patch'].items()):
                    print(f"    - {patch}: {count}")
            
            return True
        else:
            print("  ⚠️  No matches collected yet")
            print("     → Run: python quickstart.py")
            return False
            
    except Exception as e:
        print(f"  ⚠️  Unable to check data: {e}")
        return False

def check_structure():
    """Check project structure"""
    print("\nChecking project structure...")
    
    required_dirs = [
        'src/collectors',
        'src/transformers', 
        'src/storage',
        'src/utils',
        'config',
        'notebooks',
        'tests'
    ]
    
    required_files = [
        'src/collectors/match_collector.py',
        'src/transformers/schema.py',
        'src/storage/data_storage.py',
        'src/utils/riot_api_client.py',
        'requirements.txt',
        'README.md'
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).is_dir():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - MISSING")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).is_file():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_good = False
    
    return all_good

def main():
    """Run all status checks"""
    print("=" * 60)
    print("StratMancer Status Check")
    print("=" * 60)
    print()
    
    results = []
    
    # Run checks
    results.append(("Project Structure", check_structure()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Configuration", check_config()))
    results.append(("Data Collection", check_data()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! System ready.")
        print("\nNext steps:")
        print("1. python quickstart.py        # Test collection")
        print("2. python run_collector.py     # Full collection")
        print("3. jupyter notebook notebooks/validation.ipynb")
    else:
        print("⚠️  Some checks failed. Review errors above.")
        print("\nQuick fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure API key: cp .env.example .env (then edit)")
        print("3. See SETUP_GUIDE.md for detailed instructions")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

