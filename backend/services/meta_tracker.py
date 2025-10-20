"""
Meta tracker service: builds per-patch champion meta and exposes cached accessors.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from backend.services.cache import cache_service
from ml_pipeline.features import load_feature_map
from ml_pipeline.meta_utils import (
    ELO_GROUPS,
    compare_meta,
    get_latest_patch_from_api,
    load_last_patch_meta,
    normalize_patch,
    available_patches,
)

logger = logging.getLogger(__name__)


class MetaComputationError(RuntimeError):
    """Raised when meta computation fails."""


class MetaTrackerService:
    """Compute, persist, and cache meta information per ELO/patch."""

    def __init__(
        self,
        data_dir: str = "data/processed",
        meta_dir: str = "data/meta",
        feature_map_path: str = "ml_pipeline/feature_map.json",
        cache_ttl: int = 3600,
    ):
        self.data_dir = Path(data_dir)
        self.meta_dir = Path(meta_dir)
        self.cache_ttl = cache_ttl

        self.feature_map = load_feature_map(feature_map_path)
        self.champion_lookup = self._build_champion_lookup(self.feature_map)

        self.meta_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _build_champion_lookup(feature_map: Dict) -> Dict[int, str]:
        """Create champion_id -> name mapping."""
        lookup: Dict[int, str] = {}
        for name, champ_id in feature_map.get("champ_index", {}).items():
            try:
                lookup[int(champ_id)] = name
            except (TypeError, ValueError):
                continue
        return lookup

    @staticmethod
    def _normalize_elo(elo: str) -> str:
        elo_key = elo.lower()
        if elo_key in ELO_GROUPS:
            return elo_key
        # Allow direct ranks to map back into their group
        for group, ranks in ELO_GROUPS.items():
            if elo.upper() in ranks:
                return group
        raise ValueError(f"Unsupported ELO value: {elo}")

    def _rank_buckets(self, elo: str) -> List[str]:
        return ELO_GROUPS[self._normalize_elo(elo)]

    @staticmethod
    def _sorted_patches(patches: Iterable[str]) -> List[str]:
        normalized = []
        for patch in patches:
            try:
                normalized.append(normalize_patch(patch))
            except ValueError:
                continue
        unique = {patch for patch in normalized}
        return sorted(unique, key=lambda p: tuple(int(x) for x in p.split(".")), reverse=True)

    def _load_matches_for_patch(self, elo: str, patch: str) -> List[Dict]:
        patch_norm = normalize_patch(patch)
        matches: List[Dict] = []

        for rank in self._rank_buckets(elo):
            match_path = self.data_dir / f"matches_{rank}.json"
            if not match_path.exists():
                logger.debug(f"No match data for rank={rank} at {match_path}")
                continue
            try:
                with open(match_path, "r", encoding="utf-8") as handle:
                    rank_matches = json.load(handle)
            except Exception as exc:
                logger.error(f"Failed loading matches for {rank}: {exc}")
                continue

            for match in rank_matches:
                match_patch = match.get("patch")
                if not match_patch:
                    continue
                try:
                    match_patch_norm = normalize_patch(match_patch)
                except ValueError:
                    continue
                if match_patch_norm == patch_norm:
                    matches.append(match)

        return matches

    def _aggregate_stats(self, matches: Iterable[Dict]) -> Tuple[int, Dict[int, Dict[str, int]]]:
        total_matches = 0
        stats: Dict[int, Dict[str, int]] = defaultdict(lambda: {"picks": 0, "wins": 0, "bans": 0})

        for match in matches:
            total_matches += 1
            blue_win = bool(match.get("blue_win"))

            for champ_id in match.get("blue_picks", []):
                try:
                    cid = int(champ_id)
                except (TypeError, ValueError):
                    continue
                stats[cid]["picks"] += 1
                if blue_win:
                    stats[cid]["wins"] += 1

            for champ_id in match.get("red_picks", []):
                try:
                    cid = int(champ_id)
                except (TypeError, ValueError):
                    continue
                stats[cid]["picks"] += 1
                if not blue_win:
                    stats[cid]["wins"] += 1

            for champ_id in match.get("blue_bans", []):
                try:
                    cid = int(champ_id)
                except (TypeError, ValueError):
                    continue
                stats[cid]["bans"] += 1

            for champ_id in match.get("red_bans", []):
                try:
                    cid = int(champ_id)
                except (TypeError, ValueError):
                    continue
                stats[cid]["bans"] += 1

        return total_matches, stats

    def build_meta_for_patch(self, elo: str, patch: str) -> Dict:
        elo_key = self._normalize_elo(elo)
        patch_norm = normalize_patch(patch)

        matches = self._load_matches_for_patch(elo_key, patch_norm)
        if not matches:
            raise MetaComputationError(f"No matches found for elo={elo_key} patch={patch_norm}")

        total_matches, raw_stats = self._aggregate_stats(matches)

        previous_patch, previous_meta = load_last_patch_meta(elo_key, exclude_patch=patch_norm)
        prev_lookup: Dict[int, Dict] = {}
        if previous_meta:
            for entry in previous_meta.get("champions", []):
                try:
                    prev_lookup[int(entry["champion_id"])] = entry
                except (TypeError, ValueError, KeyError):
                    continue

        champions_payload: List[Dict] = []
        for champ_id, champ_name in self.champion_lookup.items():
            champ_stats = raw_stats.get(champ_id, {"picks": 0, "wins": 0, "bans": 0})
            picks = champ_stats["picks"]
            wins = champ_stats["wins"]
            bans = champ_stats["bans"]

            pick_rate = picks / total_matches if total_matches else 0.0
            win_rate = wins / picks if picks else 0.0
            ban_rate = bans / total_matches if total_matches else 0.0

            perf_index = (0.5 * win_rate) + (0.3 * (1 - ban_rate)) + (0.2 * pick_rate)

            prev_entry = prev_lookup.get(champ_id)
            prev_wr = prev_entry.get("win_rate") if prev_entry else None
            if isinstance(prev_wr, (int, float)):
                delta_wr = win_rate - prev_wr
            else:
                delta_wr = 0.0

            champions_payload.append(
                {
                    "champion_id": champ_id,
                    "champion_name": champ_name,
                    "pick_rate": round(pick_rate, 4),
                    "win_rate": round(win_rate, 4),
                    "ban_rate": round(ban_rate, 4),
                    "delta_win_rate": round(float(delta_wr), 4),
                    "performance_index": round(perf_index, 4),
                    "games_played": picks,
                    "wins": wins,
                    "bans": bans,
                }
            )

        champions_payload.sort(key=lambda item: (-item["performance_index"], item["champion_name"]))

        patches_list = self._sorted_patches([patch_norm, *available_patches(elo_key)])

        response = {
            "elo": elo_key,
            "patch": patch_norm,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_matches": total_matches,
            "champion_count": len(champions_payload),
            "previous_patch": previous_patch,
            "champions": champions_payload,
            "available_patches": patches_list,
        }

        self._persist_meta(elo_key, patch_norm, response)
        self._invalidate_cache_entries(elo_key, patch_norm)
        return response

    def _persist_meta(self, elo: str, patch: str, payload: Dict) -> None:
        elo_dir = self.meta_dir / elo
        elo_dir.mkdir(parents=True, exist_ok=True)

        meta_path = elo_dir / f"{patch}.json"
        with open(meta_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

        latest_path = self.meta_dir / f"latest_{elo}.json"
        with open(latest_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

        logger.info(f"[META] Built meta for elo={elo.capitalize()} patch={patch} ({payload['champion_count']} champs)")

    def _invalidate_cache_entries(self, elo: str, patch: str) -> None:
        cache_keys = [f"meta:{elo}:{patch}", f"meta:{elo}:latest"]
        for key in cache_keys:
            if cache_service.redis_client:
                try:
                    cache_service.redis_client.delete(key)
                except Exception as exc:
                    logger.debug(f"Failed to invalidate Redis cache {key}: {exc}")
            if key in cache_service.memory_cache:
                cache_service.memory_cache.pop(key, None)

    async def get_meta(self, elo: str, patch: str) -> Dict:
        elo_key = self._normalize_elo(elo)
        patch_norm = normalize_patch(patch)
        cache_key = f"meta:{elo_key}:{patch_norm}"

        cached = await cache_service.get(cache_key)
        if cached:
            return json.loads(cached)

        payload = self._load_meta_from_disk(elo_key, patch_norm)
        if not payload:
            raise FileNotFoundError(f"Meta data not found for elo={elo_key} patch={patch_norm}")

        await cache_service.set(cache_key, json.dumps(payload), ttl=self.cache_ttl)
        return payload

    async def get_latest_meta(self, elo: str) -> Dict:
        elo_key = self._normalize_elo(elo)
        latest_path = self.meta_dir / f"latest_{elo_key}.json"
        if latest_path.exists():
            cache_key = f"meta:{elo_key}:latest"
            cached = await cache_service.get(cache_key)
            if cached:
                return json.loads(cached)

            with open(latest_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            await cache_service.set(cache_key, json.dumps(payload), ttl=self.cache_ttl)
            return payload

        latest_patch = get_latest_patch_from_api()
        if not latest_patch:
            raise FileNotFoundError(f"No meta snapshots available for elo={elo_key}")
        payload = self.build_meta_for_patch(elo_key, latest_patch)
        await cache_service.set(f"meta:{elo_key}:latest", json.dumps(payload), ttl=self.cache_ttl)
        await cache_service.set(f"meta:{elo_key}:{normalize_patch(latest_patch)}", json.dumps(payload), ttl=self.cache_ttl)
        return payload

    async def get_trends(self, elo: str) -> Dict:
        elo_key = self._normalize_elo(elo)
        latest_meta = await self.get_latest_meta(elo_key)
        prev_patch, prev_meta = load_last_patch_meta(elo_key, exclude_patch=latest_meta.get("patch"))

        if not prev_meta:
            return {
                "elo": elo_key,
                "latest_patch": latest_meta.get("patch"),
                "previous_patch": None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "risers": [],
                "fallers": [],
            }

        delta_map = compare_meta(latest_meta, prev_meta)

        def build_entry(champion: Dict) -> Dict:
            champ_id = int(champion["champion_id"])
            delta_info = delta_map.get(champ_id, {})
            delta_wr = delta_info.get("delta_win_rate")
            if delta_wr is None:
                prev_wr = delta_info.get("previous_win_rate")
                delta_wr = champion["win_rate"] - prev_wr if isinstance(prev_wr, (int, float)) else 0.0
            prev_entry = next(
                (c for c in prev_meta.get("champions", []) if int(c["champion_id"]) == champ_id),
                None,
            )
            prev_wr = prev_entry.get("win_rate") if prev_entry else None
            return {
                "champion_id": champ_id,
                "champion_name": champion["champion_name"],
                "delta_win_rate": round(float(delta_wr or 0.0), 4),
                "current_win_rate": champion["win_rate"],
                "previous_win_rate": round(prev_wr, 4) if isinstance(prev_wr, (int, float)) else None,
                "performance_index": champion["performance_index"],
            }

        champions = [build_entry(champ) for champ in latest_meta.get("champions", [])]
        champions.sort(key=lambda item: item["delta_win_rate"], reverse=True)
        risers = champions[:10]
        fallers = sorted(champions, key=lambda item: item["delta_win_rate"])[:10]

        return {
            "elo": elo_key,
            "latest_patch": latest_meta.get("patch"),
            "previous_patch": prev_patch,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "risers": risers,
            "fallers": fallers,
        }

    def _load_meta_from_disk(self, elo: str, patch: str) -> Optional[Dict]:
        meta_path = self.meta_dir / elo / f"{patch}.json"
        if not meta_path.exists():
            return None
        with open(meta_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def refresh_all(self, patch: Optional[str] = None) -> Dict[str, Dict]:
        """
        Build the meta snapshot for every ELO group. Returns the results.
        """
        patch_to_use = normalize_patch(patch) if patch else get_latest_patch_from_api()
        if not patch_to_use:
            raise MetaComputationError("Unable to determine target patch for meta refresh")

        results: Dict[str, Dict] = {}
        for elo_key in ELO_GROUPS.keys():
            try:
                results[elo_key] = self.build_meta_for_patch(elo_key, patch_to_use)
            except MetaComputationError as exc:
                logger.warning(f"No data for elo={elo_key} patch={patch_to_use}: {exc}")
            except Exception as exc:
                logger.error(f"Failed building meta for elo={elo_key}: {exc}", exc_info=True)
        return results


# Global instance
meta_tracker = MetaTrackerService()


__all__ = [
    "meta_tracker",
    "MetaTrackerService",
    "MetaComputationError",
]
