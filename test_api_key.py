"""Test Riot API key and endpoints"""
import sys
sys.path.insert(0, '.')

from src.utils.config_manager import get_config
from src.utils.riot_api_client import RiotAPIClient
from src.utils.rate_limiter import RateLimiter

print("=" * 60)
print("Riot API Key Diagnostic Test")
print("=" * 60)

# Get config
config = get_config()
api_key = config.get_riot_api_key()
region = config.get_region()

print(f"\n1. Configuration:")
print(f"   API Key: {api_key[:20]}...{api_key[-10:]}")
print(f"   Region: {region}")

# Initialize client
rate_limiter = RateLimiter(requests_per_second=20, requests_per_2_minutes=100)
client = RiotAPIClient(api_key, region, rate_limiter)

print(f"\n2. Testing API endpoints...")

# Test 1: Get current patch (doesn't need API key)
print(f"\n   Test 1: Get current patch (Data Dragon)")
try:
    patch = client.get_current_patch()
    print(f"   ✅ Current patch: {patch}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 2: Get Challenger league (simple endpoint)
print(f"\n   Test 2: Get Challenger league")
try:
    league = client.get_challenger_league('RANKED_SOLO_5x5')
    if league:
        entries_count = len(league.get('entries', []))
        print(f"   ✅ Challenger league found: {entries_count} players")
        if entries_count > 0:
            print(f"   Sample player: {league['entries'][0].get('summonerName', 'Unknown')}")
    else:
        print(f"   ❌ No league data returned")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    if "403" in str(e) or "Forbidden" in str(e):
        print(f"   → API key is INVALID or EXPIRED")
        print(f"   → Get a new key at: https://developer.riotgames.com/")
    elif "404" in str(e):
        print(f"   → Endpoint not found (code issue)")
    elif "429" in str(e):
        print(f"   → Rate limit exceeded")

# Test 3: Get Gold league entries
print(f"\n   Test 3: Get Gold league entries (page 1)")
try:
    entries = client.get_league_entries('RANKED_SOLO_5x5', 'GOLD', 'I', page=1)
    if entries:
        print(f"   ✅ Found {len(entries)} Gold I players on page 1")
        if len(entries) > 0:
            print(f"   Sample player: {entries[0].get('summonerName', 'Unknown')}")
    else:
        print(f"   ⚠️  No entries returned (API returned empty list)")
        print(f"   This could mean:")
        print(f"   - API key might be from a different region")
        print(f"   - The endpoint returned no data (rare)")
        print(f"   - Try a different region like EUW1 or KR")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    if "403" in str(e) or "Forbidden" in str(e):
        print(f"   → API key is INVALID or EXPIRED")
        print(f"   → Get a new key at: https://developer.riotgames.com/")

print("\n" + "=" * 60)
print("Diagnosis:")
print("=" * 60)

# Summary
if "403" in str(e) or "Forbidden" in str(e):
    print("❌ API KEY ISSUE")
    print("Your API key is invalid, expired, or doesn't have permissions.")
    print("\nFix:")
    print("1. Go to: https://developer.riotgames.com/")
    print("2. Sign in")
    print("3. Generate a NEW development key")
    print("4. Update config/config.yaml or .env file")
    print("5. Note: Development keys expire after 24 hours!")
else:
    print("✅ API key appears valid")
    print("If you're still seeing issues, try:")
    print("1. Different region: python run_collector.py --region euw1")
    print("2. Different rank: python run_collector.py --ranks PLATINUM")
    print("3. Wait a moment and retry")

print("=" * 60)

