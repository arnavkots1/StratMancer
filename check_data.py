#!/usr/bin/env python3
"""Check data distribution across ranks"""

import pandas as pd
import os

ranks = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']

print("Data distribution across ranks:")
print("=" * 40)

total_matches = 0
for rank in ranks:
    file_path = f"data/processed/matches_{rank}.parquet"
    if os.path.exists(file_path):
        df = pd.read_parquet(file_path)
        count = len(df)
        total_matches += count
        print(f"{rank:12}: {count:6,} matches")
    else:
        print(f"{rank:12}: No data file")

print("=" * 40)
print(f"{'TOTAL':12}: {total_matches:6,} matches")

# Check ELO group totals
elo_groups = {
    'low': ['IRON', 'BRONZE', 'SILVER'],
    'mid': ['GOLD', 'PLATINUM', 'EMERALD'], 
    'high': ['DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
}

print("\nELO Group totals:")
print("=" * 20)
for group, group_ranks in elo_groups.items():
    group_total = 0
    for rank in group_ranks:
        file_path = f"data/processed/matches_{rank}.parquet"
        if os.path.exists(file_path):
            df = pd.read_parquet(file_path)
            group_total += len(df)
    print(f"{group:4}: {group_total:6,} matches")

