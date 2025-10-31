"""
Patch note featurizer service using Gemini AI.
Parses Riot patch notes and converts them into structured champion features.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

import requests
from bs4 import BeautifulSoup

from backend.services.cache import cache_service
from ml_pipeline.meta_utils import normalize_patch

logger = logging.getLogger(__name__)

# Gemini system prompt
GEMINI_SYSTEM_PROMPT = """You are StratMancer's Patch Featurizer AI.

Input: League of Legends official patch note text.

Output: STRICT JSON describing buffs, nerfs, and meta tags per champion.

Rules:
- Summarize each champion's adjustments numerically (approximate ±% if mentioned).
- Tag gameplay aspects: damage, ability haste, CC, survivability, healing, scaling, mobility.
- Output JSON schema:
{
  "patch": "14.21",
  "champions": [
    {
      "name": "Ahri",
      "category": "Buff|Nerf|Adjust",
      "impact": +2.5,
      "affected_tags": ["burst", "mobility"],
      "notes": "Slight buff to early Q damage and mana efficiency."
    }
  ]
}

Never include prose outside JSON. Use numeric impact estimates even if inferred qualitatively."""

# Champion name mapping (to handle variations)
CHAMPION_NAMES = {}  # Will be loaded from feature map


class PatchNoteFeaturizer:
    """Service for extracting structured features from Riot patch notes."""

    def __init__(self):
        # Get API key from settings (which loads from .env) or fallback to os.getenv
        try:
            from backend.config import settings
            self.api_key: Optional[str] = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        except Exception:
            # Fallback if settings not available
            self.api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        
        self.cache_dir = Path("data/patch_features")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if HAS_GEMINI and self.api_key:
            genai.configure(api_key=self.api_key)
            # Use the correct model name (full path required)
            self.model = genai.GenerativeModel('models/gemini-flash-latest')
            logger.info("Gemini AI initialized for patch note featurization")
        else:
            self.model = None
            if not HAS_GEMINI:
                logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")
            if not self.api_key:
                logger.warning("GEMINI_API_KEY not set. Patch note featurization will use fallback heuristics.")

    def fetch_patch_notes(self, patch: str) -> Optional[str]:
        """
        Fetch patch notes from Riot's website.
        
        Args:
            patch: Patch version (e.g., "14.21")
            
        Returns:
            Raw patch note text or None if fetch fails
        """
        try:
            # Try multiple URL patterns
            urls = [
                f"https://www.leagueoflegends.com/en-us/news/game-updates/patch-{patch}-notes/",
                f"https://www.leagueoflegends.com/en-us/news/game-updates/patch-{patch}/",
                f"https://www.leagueoflegends.com/en-us/news/game-updates/patch-{patch.replace('.', '-')}-notes/",
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        # Extract main content
                        content = soup.find('article') or soup.find('main') or soup.find('body')
                        if content:
                            text = content.get_text(separator='\n', strip=True)
                            logger.info(f"Fetched patch notes for {patch} from {url}")
                            return text
                except Exception as e:
                    logger.debug(f"Failed to fetch from {url}: {e}")
                    continue
                    
            logger.warning(f"Could not fetch patch notes for {patch} from any URL")
            return None
        except Exception as e:
            logger.error(f"Error fetching patch notes: {e}")
            return None

    async def extract_features_with_gemini(self, patch_text: str, patch: str) -> Optional[Dict[str, Any]]:
        """
        Use Gemini to extract structured features from patch notes.
        
        Args:
            patch_text: Raw patch note text
            patch: Patch version
            
        Returns:
            Structured JSON dict or None if extraction fails
        """
        if not self.model:
            logger.warning("Gemini model not initialized, cannot extract features")
            return None
            
        try:
            prompt = f"{GEMINI_SYSTEM_PROMPT}\n\nPatch Notes Text:\n{patch_text[:5000]}"  # Limit prompt size
            
            logger.info(f"Calling Gemini API for patch {patch}...")
            
            # Call Gemini with timeout (use sync if async not available)
            try:
                # Try async first
                if hasattr(self.model, 'generate_content_async'):
                    response = await asyncio.wait_for(
                        self.model.generate_content_async(prompt),
                        timeout=10.0
                    )
                else:
                    # Fallback to sync in executor
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.model.generate_content(prompt)
                    )
            except AttributeError as e:
                logger.warning(f"Async method not available, using sync: {e}")
                # Fallback to sync if async method not available
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt)
                )
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}", exc_info=True)
                return None
            
            if not response or not hasattr(response, 'text'):
                logger.error("Gemini returned invalid response (no text attribute)")
                return None
                
            text = response.text.strip()
            logger.debug(f"Gemini response length: {len(text)} chars")
            
            # Extract JSON from response (might be wrapped in markdown code blocks)
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = text
                
            result = json.loads(json_str)
            result['patch'] = normalize_patch(patch)
            
            logger.info(f"Gemini extracted features for {len(result.get('champions', []))} champions")
            return result
            
        except asyncio.TimeoutError:
            logger.error("Gemini API timeout after 10s")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            if 'text' in locals():
                logger.debug(f"Response text (first 500 chars): {text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}", exc_info=True)
            return None

    def extract_features_heuristic(self, patch_text: str, patch: str) -> Dict[str, Any]:
        """
        Fallback heuristic extraction when Gemini is unavailable.
        
        Args:
            patch_text: Raw patch note text
            patch: Patch version
            
        Returns:
            Basic structured dict with keyword-based detection
        """
        patch_norm = normalize_patch(patch)
        champions = []
        
        # Simple keyword-based detection
        lines = patch_text.lower().split('\n')
        current_champion = None
        
        for line in lines:
            # Look for champion mentions (simplified)
            if 'buff' in line or 'increased' in line or 'improved' in line:
                # Try to extract champion name
                for word in line.split():
                    if word.isalpha() and len(word) > 3:
                        champions.append({
                            "name": word.capitalize(),
                            "category": "Buff",
                            "impact": 0.1,  # Default small buff
                            "affected_tags": ["damage"],
                            "notes": line[:200]
                        })
                        break
            elif 'nerf' in line or 'decreased' in line or 'reduced' in line:
                for word in line.split():
                    if word.isalpha() and len(word) > 3:
                        champions.append({
                            "name": word.capitalize(),
                            "category": "Nerf",
                            "impact": -0.1,  # Default small nerf
                            "affected_tags": ["damage"],
                            "notes": line[:200]
                        })
                        break
                        
        return {
            "patch": patch_norm,
            "champions": champions if champions else []
        }

    def get_champion_id_mapping(self) -> Dict[str, int]:
        """Load champion name to ID mapping from feature map."""
        try:
            from ml_pipeline.features import load_feature_map
            feature_map = load_feature_map()
            tags = feature_map.get('tags', {})
            
            mapping = {}
            for champ_id, champ_data in tags.items():
                name = champ_data.get('name', '').lower()
                if name:
                    mapping[name] = int(champ_id)
            return mapping
        except Exception as e:
            logger.warning(f"Could not load champion mapping: {e}")
            return {}

    def convert_to_prior_features(self, features: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        """
        Convert Gemini output to champion ID -> impact mapping.
        
        Args:
            features: Gemini output JSON
            
        Returns:
            Dict mapping champion_id -> {impact: float, tags: List[str]}
        """
        champion_map = self.get_champion_id_mapping()
        priors = {}
        
        for champ_entry in features.get('champions', []):
            name = champ_entry.get('name', '').lower()
            impact = champ_entry.get('impact', 0.0)
            tags = champ_entry.get('affected_tags', [])
            
            # Find champion ID
            champ_id = champion_map.get(name)
            if not champ_id:
                # Try fuzzy match
                for mapped_name, mapped_id in champion_map.items():
                    if name in mapped_name or mapped_name in name:
                        champ_id = mapped_id
                        break
                        
            if champ_id:
                # Normalize impact to -1..+1 range
                normalized_impact = max(-1.0, min(1.0, impact / 100.0 if abs(impact) > 1 else impact))
                priors[champ_id] = {
                    "impact": normalized_impact,
                    "tags": tags,
                    "category": champ_entry.get('category', 'Adjust'),
                    "notes": champ_entry.get('notes', '')
                }
                
        logger.info(f"Converted {len(priors)} champions to prior features")
        return priors

    async def get_patch_features(self, patch: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get structured features for a patch.
        
        Args:
            patch: Patch version (e.g., "14.21")
            use_cache: Whether to use cached results
            
        Returns:
            Dict with patch features including champion impacts
        """
        patch_norm = normalize_patch(patch)
        cache_file = self.cache_dir / f"patch_{patch_norm}.json"
        
        # Check cache first
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                logger.info(f"Loaded cached patch features for {patch_norm}")
                return cached
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        # Check Redis cache
        cache_key = f"patch_features:{patch_norm}"
        if use_cache:
            cached = await cache_service.get(cache_key)
            if cached:
                try:
                    # Cache stores JSON string, parse it
                    cached_data = json.loads(cached)
                    logger.info(f"Loaded patch features from Redis cache for {patch_norm}")
                    return cached_data
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse cached data: {e}")
                    # Continue to fetch fresh data
        
        # Fetch patch notes
        patch_text = self.fetch_patch_notes(patch)
        if not patch_text:
            logger.warning(f"Could not fetch patch notes for {patch_norm} from Riot website")
            # Return empty structure but don't fail - user can still see it's being processed
            return {
                "patch": patch_norm,
                "champions": [],
                "source": "none",
                "priors": {},
                "message": "Patch notes could not be fetched. This patch may not exist or patch notes may not be available yet."
            }
        
        # Extract features
        try:
            if self.model:
                logger.info(f"Attempting Gemini extraction for patch {patch_norm}")
                features = await self.extract_features_with_gemini(patch_text, patch)
                if features:
                    source = "gemini"
                    logger.info(f"Successfully extracted features using Gemini")
                else:
                    logger.warning(f"Gemini extraction returned None for {patch_norm}, falling back to heuristic")
                    features = self.extract_features_heuristic(patch_text, patch)
                    source = "heuristic"
            else:
                logger.info(f"Gemini model not available, using heuristic extraction")
                features = self.extract_features_heuristic(patch_text, patch)
                source = "heuristic"
                
            if not features:
                logger.warning(f"Feature extraction returned None for {patch_norm}, using empty heuristic fallback")
                features = self.extract_features_heuristic(patch_text, patch)
                source = "heuristic"
        except Exception as e:
            logger.error(f"Error extracting features from patch notes: {e}", exc_info=True)
            # Fallback to heuristic
            features = self.extract_features_heuristic(patch_text, patch)
            source = "heuristic"
            
        if not features:
            features = {"patch": patch_norm, "champions": []}
            source = "heuristic"
            
        features['source'] = source
        features['priors'] = self.convert_to_prior_features(features)
        
        # Cache results
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(features, f, indent=2)
            logger.info(f"Cached patch features to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache to file: {e}")
            
        # Cache in Redis (TTL 24h)
        try:
            # Cache stores JSON strings
            await cache_service.set(cache_key, json.dumps(features), ttl=86400)
        except Exception:
            pass  # Redis might not be available
            
        return features

    async def get_champion_prior(self, patch: str, champion_id: int) -> float:
        """
        Get normalized impact prior for a specific champion.
        
        Args:
            patch: Patch version
            champion_id: Champion ID
            
        Returns:
            Impact value (-1 to +1) or 0.0 if not found
        """
        features = await self.get_patch_features(patch)
        priors = features.get('priors', {})
        champ_prior = priors.get(champion_id, {})
        return champ_prior.get('impact', 0.0) if isinstance(champ_prior, dict) else 0.0


# Global instance
patchnote_featurizer = PatchNoteFeaturizer()

