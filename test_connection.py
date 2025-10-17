"""Test network connection to Riot API"""
import requests
import sys

print("Testing connection to Riot API...")
print("-" * 50)

# Test basic internet
print("\n1. Testing basic internet connectivity...")
try:
    response = requests.get("https://www.google.com", timeout=5)
    print(f"   ✅ Internet connection: OK (Status {response.status_code})")
except Exception as e:
    print(f"   ❌ No internet connection: {e}")
    sys.exit(1)

# Test Riot API (Data Dragon - doesn't need API key)
print("\n2. Testing Riot servers (Data Dragon)...")
try:
    response = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=5)
    if response.status_code == 200:
        versions = response.json()
        print(f"   ✅ Riot Data Dragon: OK")
        print(f"   Current patch: {versions[0]}")
    else:
        print(f"   ⚠️ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Cannot reach Riot servers: {e}")
    print("   → This is likely a firewall or network restriction")

# Test Riot API endpoint
print("\n3. Testing Riot API endpoint...")
try:
    # This will fail without a valid API key, but tests connectivity
    response = requests.get("https://na1.api.riotgames.com/lol/status/v4/platform-data", timeout=5)
    print(f"   ✅ Can reach Riot API servers (Status {response.status_code})")
    if response.status_code == 403:
        print("   Note: 403 is expected without API key - connection is working!")
except requests.exceptions.ConnectionError as e:
    print(f"   ❌ Cannot connect to Riot API: {e}")
    print("\n" + "=" * 50)
    print("DIAGNOSIS:")
    print("- Your firewall/antivirus is likely blocking the connection")
    print("- Or your network restricts access to gaming APIs")
    print("\nSOLUTIONS:")
    print("1. Try a different network (mobile hotspot)")
    print("2. Disable firewall temporarily and test")
    print("3. Add Python to firewall exceptions")
    print("=" * 50)
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "-" * 50)
print("Test complete!")

