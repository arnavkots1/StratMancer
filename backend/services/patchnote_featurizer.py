"""
Patch Analysis service using Gemini AI.
Analyzes our collected match data to explain meta shifts and champion balance changes.
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

from backend.services.cache import cache_service
from backend.services.meta_tracker import meta_tracker
from ml_pipeline.meta_utils import normalize_patch

logger = logging.getLogger(__name__)

# Gemini system prompt for analyzing meta data
GEMINI_SYSTEM_PROMPT = """You are StratMancer's Patch Analysis AI.

Input: Champion performance data comparing current patch vs previous patch.

Your task: Analyze which champions got BETTER or WORSE and explain WHY in strategic terms.

For each champion showing significant change:
- Categorize as "Buff" (got better), "Nerf" (got worse), or "Adjust" (mixed/neutral)
- Calculate impact score (-100 to +100): Based on win rate delta, pick rate change, ban rate change
- Explain WHY: What changed? Why did win rate improve/decline? Strategic implications?
- Tag affected gameplay aspects: burst, mobility, survivability, scaling, cc, damage, healing, etc.

Output STRICT JSON:
{
  "patch": "15.20",
  "champions": [
    {
      "name": "Ahri",
      "category": "Buff|Nerf|Adjust",
      "impact": 15.5,
      "affected_tags": ["burst", "mobility"],
      "notes": "Win rate increased 3.2% with 12% pick rate increase. Likely benefited from meta shifts favoring mobile mages. Stronger laning phase and mid-game skirmish presence."
    }
  ]
}

Focus on champions with |delta_win_rate| > 0.02 or significant pick rate changes (>20% relative change).
Explain strategic implications: Why is this good/bad? What playstyles benefit? What counters emerged?

Never include prose outside JSON. Be specific about WHY champions changed."""

# Champion name mapping (to handle variations)
CHAMPION_NAMES = {}  # Will be loaded from feature map


class MetaAnalyzer:
    """Service for analyzing patch changes using our collected match data and Gemini AI."""

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

    def _prepare_meta_comparison(self, elo: str, patch: str) -> Optional[Dict[str, Any]]:
        """
        Load current and previous patch meta data for comparison.
        
        Args:
            elo: ELO group (low, mid, high)
            patch: Patch version (e.g., "15.20")
            
        Returns:
            Dict with current and previous meta data, or None if unavailable
        """
        try:
            patch_norm = normalize_patch(patch)
            
            # Get current patch meta - try patch-specific file first, then latest
            current_meta = meta_tracker._load_meta_from_disk(elo, patch_norm)
            if not current_meta:
                # Fallback to latest meta if patch-specific doesn't exist
                logger.info(f"Patch-specific meta not found, trying latest for {elo}")
                try:
                    # Load latest meta directly from disk
                    latest_path = meta_tracker.meta_dir / f"latest_{elo}.json"
                    if latest_path.exists():
                        import json
                        with open(latest_path, 'r', encoding='utf-8') as f:
                            current_meta = json.load(f)
                        if current_meta and current_meta.get("patch") != patch_norm:
                            logger.warning(f"Latest meta is for patch {current_meta.get('patch')}, not {patch_norm}")
                except Exception as e:
                    logger.warning(f"Could not load latest meta: {e}")
            
            if not current_meta:
                logger.warning(f"No meta data found for {elo} patch {patch_norm}")
                return None
            
            # Get previous patch meta
            from ml_pipeline.meta_utils import load_last_patch_meta
            prev_patch, prev_meta = load_last_patch_meta(elo, exclude_patch=patch_norm)
            
            if not prev_meta:
                logger.info(f"No previous patch meta found for comparison")
                # Still return current meta for analysis
                return {
                    "current_patch": patch_norm,
                    "previous_patch": None,
                    "current_meta": current_meta,
                    "previous_meta": None
                }
            
            return {
                "current_patch": patch_norm,
                "previous_patch": prev_patch,
                "current_meta": current_meta,
                "previous_meta": prev_meta
            }
        except Exception as e:
            logger.error(f"Error preparing meta comparison: {e}", exc_info=True)
            return None
    
    def _format_meta_for_gemini(self, comparison: Dict[str, Any]) -> str:
        """
        Format meta comparison data into a readable format for Gemini.
        
        Returns:
            Formatted text describing champion changes
        """
        current = comparison["current_meta"]
        previous = comparison.get("previous_meta")
        
        if not previous:
            # Only current patch data available
            text = f"Meta snapshot for patch {comparison['current_patch']}:\n\n"
            text += f"Total matches: {current.get('total_matches', 0)}\n"
            text += "Top performers:\n"
            for champ in current.get("champions", [])[:20]:
                text += f"- {champ['champion_name']}: WR {champ['win_rate']:.1%}, PR {champ['pick_rate']:.1%}, BR {champ['ban_rate']:.1%}\n"
            return text
        
        # Compare with previous patch
        prev_lookup = {c["champion_id"]: c for c in previous.get("champions", [])}
        
        text = f"Patch Analysis: Patch {comparison['current_patch']} vs {comparison['previous_patch']}\n\n"
        text += f"Current patch: {current.get('total_matches', 0)} matches analyzed\n"
        text += f"Previous patch: {previous.get('total_matches', 0)} matches analyzed\n\n"
        text += "Champion Changes:\n"
        
        significant_changes = []
        for champ in current.get("champions", []):
            champ_id = champ["champion_id"]
            prev_champ = prev_lookup.get(champ_id)
            
            if prev_champ:
                delta_wr = champ.get("delta_win_rate", 0)
                prev_wr = prev_champ.get("win_rate", 0)
                prev_pr = prev_champ.get("pick_rate", 0)
                curr_pr = champ.get("pick_rate", 0)
                prev_br = prev_champ.get("ban_rate", 0)
                curr_br = champ.get("ban_rate", 0)
                
                pr_change = curr_pr - prev_pr
                br_change = curr_br - prev_br
                
                # Include champions with significant changes
                if abs(delta_wr) > 0.02 or abs(pr_change) > 0.05 or abs(br_change) > 0.03:
                    significant_changes.append({
                        "name": champ["champion_name"],
                        "current_wr": champ["win_rate"],
                        "prev_wr": prev_wr,
                        "delta_wr": delta_wr,
                        "current_pr": curr_pr,
                        "prev_pr": prev_pr,
                        "pr_change": pr_change,
                        "current_br": curr_br,
                        "prev_br": prev_br,
                        "br_change": br_change,
                        "games": champ.get("games_played", 0)
                    })
        
        # Sort by absolute win rate change
        significant_changes.sort(key=lambda x: abs(x["delta_wr"]), reverse=True)
        
        for change in significant_changes[:30]:  # Top 30 changes
            text += f"\n{change['name']}:\n"
            text += f"  Win Rate: {change['prev_wr']:.1%} → {change['current_wr']:.1%} (Δ {change['delta_wr']:+.1%})\n"
            text += f"  Pick Rate: {change['prev_pr']:.1%} → {change['current_pr']:.1%} (Δ {change['pr_change']:+.1%})\n"
            text += f"  Ban Rate: {change['prev_br']:.1%} → {change['current_br']:.1%} (Δ {change['br_change']:+.1%})\n"
            text += f"  Games: {change['games']}\n"
        
        return text

    async def extract_features_with_gemini(self, meta_comparison_text: str, patch: str) -> Optional[Dict[str, Any]]:
        """
        Use Gemini to analyze meta changes and explain what's good/bad and why.
        
        Args:
            meta_comparison_text: Formatted meta comparison data
            patch: Patch version
            
        Returns:
            Structured JSON dict or None if extraction fails
        """
        if not self.model:
            logger.warning("Gemini model not initialized, cannot analyze meta")
            return None
            
        try:
            prompt = f"{GEMINI_SYSTEM_PROMPT}\n\nMeta Comparison Data:\n{meta_comparison_text}"
            
            logger.info(f"Calling Gemini API for patch {patch}...")
            
            # Call Gemini with timeout (use sync if async not available)
            try:
                # Try async first
                if hasattr(self.model, 'generate_content_async'):
                    response = await asyncio.wait_for(
                        self.model.generate_content_async(prompt),
                        timeout=30.0  # Increased timeout for complex patch analysis
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
    
    def _extract_features_heuristic_from_meta(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Heuristic extraction from meta comparison when Gemini unavailable."""
        current = comparison["current_meta"]
        previous = comparison.get("previous_meta")
        patch_norm = comparison["current_patch"]
        
        champions = []
        
        if not current or not current.get("champions"):
            logger.warning(f"No champion data in current meta for patch {patch_norm}")
            return {"patch": patch_norm, "champions": []}
        
        if previous and previous.get("champions"):
            prev_lookup = {c["champion_id"]: c for c in previous.get("champions", [])}
            
            for champ in current.get("champions", []):
                champ_id = champ.get("champion_id")
                if not champ_id:
                    continue
                    
                prev_champ = prev_lookup.get(champ_id)
                
                if prev_champ:
                    # Use delta_win_rate if available, otherwise calculate
                    delta_wr = champ.get("delta_win_rate")
                    if delta_wr is None:
                        prev_wr = prev_champ.get("win_rate", 0)
                        curr_wr = champ.get("win_rate", 0)
                        delta_wr = curr_wr - prev_wr
                    
                    # Lower threshold to catch more changes
                    if abs(delta_wr) > 0.01:  # 1% change threshold (lowered from 2%)
                        category = "Buff" if delta_wr > 0 else "Nerf"
                        # Impact as percentage
                        impact = delta_wr * 100
                        
                        # Also check pick rate changes
                        prev_pr = prev_champ.get("pick_rate", 0)
                        curr_pr = champ.get("pick_rate", 0)
                        pr_change = curr_pr - prev_pr
                        
                        notes = f"Win rate: {prev_champ.get('win_rate', 0):.1%} → {champ.get('win_rate', 0):.1%} (Δ {delta_wr:+.1%})"
                        if abs(pr_change) > 0.01:
                            notes += f". Pick rate: {prev_pr:.1%} → {curr_pr:.1%} (Δ {pr_change:+.1%})"
                        
                        champions.append({
                            "name": champ.get("champion_name", "Unknown"),
                            "category": category,
                            "impact": impact,
                            "affected_tags": ["meta"],
                            "notes": notes
                        })
            
            # If we still have no champions, include top risers/fallers anyway
            if not champions:
                logger.info("No champions met threshold, including top 20 changes anyway")
                sorted_champs = sorted(
                    current.get("champions", []),
                    key=lambda c: abs(c.get("delta_win_rate", 0)),
                    reverse=True
                )
                for champ in sorted_champs[:20]:
                    delta_wr = champ.get("delta_win_rate", 0)
                    if abs(delta_wr) > 0:
                        champions.append({
                            "name": champ.get("champion_name", "Unknown"),
                            "category": "Buff" if delta_wr > 0 else "Nerf",
                            "impact": delta_wr * 100,
                            "affected_tags": ["meta"],
                            "notes": f"Win rate delta: {delta_wr:+.1%}"
                        })
        else:
            # No previous patch, list top performers
            logger.info("No previous patch data, listing top performers")
            champs_list = current.get("champions", [])
            logger.info(f"Found {len(champs_list)} champions in current meta")
            
            if not champs_list:
                logger.warning(f"No champions found in current meta data")
                return {"patch": patch_norm, "champions": []}
            
            # Sort by performance index or win rate
            sorted_champs = sorted(
                champs_list,
                key=lambda c: c.get("performance_index", c.get("win_rate", 0)),
                reverse=True
            )
            
            for champ in sorted_champs[:30]:
                champ_name = champ.get("champion_name") or champ.get("name", "Unknown")
                wr = champ.get("win_rate", 0.5)
                pr = champ.get("pick_rate", 0)
                
                champions.append({
                    "name": champ_name,
                    "category": "Adjust",
                    "impact": (wr - 0.5) * 100,  # Deviation from 50%
                    "affected_tags": ["meta"],
                    "notes": f"Win rate: {wr:.1%}, Pick rate: {pr:.1%}, Performance Index: {champ.get('performance_index', 0):.2f}"
                })
        
        logger.info(f"Heuristic extraction found {len(champions)} champions for patch {patch_norm}")
        return {
            "patch": patch_norm,
            "champions": champions
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

    async def get_patch_features(self, patch: str, elo: str = "mid", use_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze meta changes for a patch using our collected match data.
        
        Args:
            patch: Patch version (e.g., "15.20")
            elo: ELO group (low, mid, high) - defaults to "mid"
            use_cache: Whether to use cached results
            
        Returns:
            Dict with patch analysis including champion impacts and explanations
        """
        patch_norm = normalize_patch(patch)
        elo_key = elo.lower()
        cache_file = self.cache_dir / f"meta_analysis_{elo_key}_{patch_norm}.json"
        
        # Check cache first (includes synergies, so no recalculation needed - saves tokens)
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                # If cached data has synergies, return it (avoids recalculation and saves tokens)
                if cached.get('synergies') is not None:
                    logger.info(f"Loaded cached patch analysis with synergies for {elo_key} patch {patch_norm}")
                    return cached
                # If no synergies in cache, we'll add them below (but won't call Gemini again)
                logger.info(f"Loaded cached patch analysis (will add synergies) for {elo_key} patch {patch_norm}")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        # Check Redis cache (also includes synergies - saves tokens)
        cache_key = f"meta_analysis:{elo_key}:{patch_norm}"
        if use_cache:
            cached = await cache_service.get(cache_key)
            if cached:
                try:
                    cached_data = json.loads(cached)
                    # If Redis cache has synergies, return it (avoids recalculation)
                    if cached_data.get('synergies') is not None:
                        logger.info(f"Loaded patch analysis with synergies from Redis cache for {elo_key} patch {patch_norm}")
                        return cached_data
                    # If no synergies, we'll add them but won't call Gemini again
                    logger.info(f"Loaded patch analysis from Redis cache (will add synergies) for {elo_key} patch {patch_norm}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse cached data: {e}")
        
        # Prepare meta comparison
        logger.info(f"Preparing patch analysis for {elo_key} patch {patch_norm}")
        comparison = self._prepare_meta_comparison(elo_key, patch_norm)
        
        if not comparison:
            logger.warning(f"No meta data available for {elo_key} patch {patch_norm}")
            return {
                "patch": patch_norm,
                "champions": [],
                "source": "none",
                "priors": {},
                "message": f"No meta data found for patch {patch_norm}. Meta snapshots need to be built first using the meta tracker."
            }
        
        # Format meta data for Gemini
        meta_text = self._format_meta_for_gemini(comparison)
        
        # Analyze with Gemini
        try:
            if self.model:
                logger.info(f"Attempting Gemini analysis for {elo_key} patch {patch_norm}")
                features = await self.extract_features_with_gemini(meta_text, patch_norm)
                if features:
                    source = "gemini"
                    logger.info(f"Successfully analyzed meta using Gemini")
                else:
                    logger.warning(f"Gemini analysis returned None, falling back to heuristic")
                    features = self._extract_features_heuristic_from_meta(comparison)
                    source = "heuristic"
            else:
                logger.info(f"Gemini model not available, using heuristic extraction")
                features = self._extract_features_heuristic_from_meta(comparison)
                source = "heuristic"
                
            if not features:
                features = {"patch": patch_norm, "champions": []}
                source = "heuristic"
        except Exception as e:
            logger.error(f"Error analyzing meta: {e}", exc_info=True)
            features = self._extract_features_heuristic_from_meta(comparison)
            source = "heuristic"
            
        if not features:
            features = {"patch": patch_norm, "champions": []}
            source = "heuristic"
            
        features['source'] = source
        features['priors'] = self.convert_to_prior_features(features)
        
        # Add synergy analysis for top champions (only if not cached, uses local data - no tokens)
        # Only analyze for champions that are in the features list to minimize work
        if features.get('champions'):
            # Limit to top 5 champions to reduce computation
            top_champ_ids = [champ.get('champion_id') for champ in features['champions'][:5] if champ.get('champion_id')]
            features['synergies'] = await self._analyze_champion_synergies(comparison, elo_key, limit_champions=top_champ_ids)
        else:
            features['synergies'] = {}
        
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

    async def _analyze_champion_synergies(self, comparison: Dict[str, Any], elo: str, limit_champions: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Analyze synergies for top meta champions.
        Uses local history index data - NO API tokens used.
        
        Args:
            comparison: Meta comparison data
            elo: ELO group
            limit_champions: Optional list of champion IDs to analyze (if provided, only analyze these)
            
        Returns:
            Dict mapping champion_id -> list of best synergy pairs with explanations
        """
        try:
            from ml_pipeline.features.history_index import HistoryIndex
            from ml_pipeline.features import load_feature_map
            
            # Load history index
            history_index = HistoryIndex()
            history_index.load("ml_pipeline/history_index.json")
            
            # Load feature map for champion name lookup
            feature_map = load_feature_map()
            champ_index = feature_map.get('champ_index', {})
            id_to_name = {int(v): k for k, v in champ_index.items()}
            
            current = comparison.get("current_meta", {})
            champions = current.get("champions", [])
            
            if not champions:
                return {}
            
            # Determine which champions to analyze
            # If limit_champions provided, use only those (to minimize work)
            if limit_champions:
                champions_to_analyze = [c for c in champions if c.get("champion_id") in limit_champions]
                # Limit to max 5 champions
                champions_to_analyze = champions_to_analyze[:5]
            else:
                # Default: analyze top 5 champions
                previous = comparison.get("previous_meta")
                
                if previous and previous.get("champions"):
                    # Use top 5 altered champions (if previous patch exists)
                    prev_lookup = {c["champion_id"]: c for c in previous.get("champions", [])}
                    
                    altered_champions = []
                    for champ in champions:
                        champ_id = champ.get("champion_id")
                        if champ_id and champ_id in prev_lookup:
                            delta_wr = abs(champ.get("delta_win_rate", 0))
                            altered_champions.append((champ_id, delta_wr, champ))
                    
                    # Sort by delta win rate and take top 5
                    altered_champions.sort(key=lambda x: x[1], reverse=True)
                    champions_to_analyze = [x[2] for x in altered_champions[:5]]
                else:
                    # Use top 5 meta champions by performance index
                    sorted_champions = sorted(
                        champions,
                        key=lambda c: c.get("performance_index", 0),
                        reverse=True
                    )
                    champions_to_analyze = sorted_champions[:5]
            
            # Map ELO group to representative rank for history index
            # History index uses specific ranks, so we pick a representative from each group
            from ml_pipeline.meta_utils import ELO_GROUPS
            elo_group = elo.lower()
            if elo_group in ELO_GROUPS:
                # Use the first rank in the group as representative
                rank = ELO_GROUPS[elo_group][0]  # e.g., "GOLD" for mid, "IRON" for low
            else:
                rank = "GOLD"  # Default fallback
            
            synergies_dict = {}
            
            for champ in champions_to_analyze:
                champ_id = champ.get("champion_id")
                champ_name = champ.get("champion_name", id_to_name.get(champ_id, "Unknown"))
                
                if not champ_id or rank not in history_index.elo_indices:
                    continue
                
                index = history_index.elo_indices[rank]
                pair_wr = index['pair_wr']
                champ_wr = index['champ_wr']
                avg_wr = index['avg_wr']
                
                # Find all pairs involving this champion
                champ_synergies = []
                
                for (c1, c2), pair_wr_value in pair_wr.items():
                    if c1 == champ_id or c2 == champ_id:
                        partner_id = c2 if c1 == champ_id else c1
                        partner_name = id_to_name.get(partner_id, f"Champ {partner_id}")
                        
                        # Calculate synergy score
                        champ_wr_value = champ_wr.get(champ_id, avg_wr)
                        partner_wr_value = champ_wr.get(partner_id, avg_wr)
                        expected_wr = (champ_wr_value + partner_wr_value) / 2
                        synergy_score = pair_wr_value - expected_wr
                        
                        champ_synergies.append({
                            "champion_id": partner_id,
                            "champion_name": partner_name,
                            "win_rate": round(pair_wr_value, 4),
                            "synergy_score": round(synergy_score, 4)
                        })
                
                # Sort by synergy score (best synergies first)
                champ_synergies.sort(key=lambda x: x["synergy_score"], reverse=True)
                
                # Take top 3 synergies only (to minimize data size)
                top_synergies = champ_synergies[:3]
                
                if top_synergies:
                    synergies_dict[str(champ_id)] = {
                        "champion_name": champ_name,
                        "synergies": top_synergies,
                        "explanation": self._generate_synergy_explanation(champ_name, top_synergies)
                    }
            
            return synergies_dict
            
        except Exception as e:
            logger.error(f"Failed to analyze synergies: {e}", exc_info=True)
            return {}
    
    def _generate_synergy_explanation(self, champ_name: str, synergies: List[Dict]) -> str:
        """Generate explanation text for champion synergies."""
        if not synergies:
            return f"No strong synergy data available for {champ_name}."
        
        best_synergy = synergies[0]
        partner = best_synergy["champion_name"]
        synergy_score = best_synergy["synergy_score"]
        wr = best_synergy["win_rate"]
        
        if synergy_score > 0.05:
            strength = "exceptionally strong"
        elif synergy_score > 0.02:
            strength = "strong"
        else:
            strength = "good"
        
        explanation = f"{champ_name} pairs {strength} with {partner} "
        explanation += f"(win rate: {wr:.1%}, synergy: +{synergy_score*100:.1f}%)."
        
        # Only mention one additional partner to keep explanation short
        if len(synergies) > 1:
            other_partner = synergies[1]["champion_name"]
            explanation += f" Also pairs well with {other_partner}."
        
        return explanation
    
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


# Global instance (keeping old name for backwards compatibility)
meta_analyzer = MetaAnalyzer()
patchnote_featurizer = meta_analyzer  # Alias for backwards compatibility

