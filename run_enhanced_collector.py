"""
Main entry point for running the enhanced match data collector.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.collectors.enhanced_collector import main

if __name__ == '__main__':
    sys.exit(main())

