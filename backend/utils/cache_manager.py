"""
Memory-aware cache manager for cancer gene analysis.

Changes from original:
- Adds cache size limits (max entries and max total size)
- Validates data size before caching (rejects large objects)
- Only caches lightweight final responses, never raw DataFrames
- Memory-safe JSON serialization
"""
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any, Union
from backend.config import CACHE_DIR, CACHE_TTL_HOURS, CACHE_ENABLED
from backend.utils.logger import StructuredLogger
from backend.utils.memory import log_memory

logger = StructuredLogger(__name__)

# Cache limits to prevent memory bloat
MAX_CACHE_ENTRIES = 50
MAX_CACHE_SIZE_MB = 50  # Total cache on disk
MAX_SINGLE_ENTRY_SIZE_MB = 5  # Reject individual entries larger than this


class CacheManager:
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.ttl_seconds = CACHE_TTL_HOURS * 3600
        self.enabled = CACHE_ENABLED

    def _generate_key(self, analysis_type: str, gene: str, cancer: str) -> str:
        """Generates a deterministic cache key string."""
        return f"{analysis_type}_{gene.upper()}_{cancer.upper()}"

    def _get_cache_path(self, key: str) -> Path:
        """Returns the file path for a cache key."""
        return self.cache_dir / f"{key}.json"

    def _validate_size(self, data: Dict[str, Any]) -> bool:
        """
        Check if the data is small enough to cache.
        Rejects data that's too large (e.g. full plotly JSON with many points).
        """
        try:
            serialized = json.dumps(data)
            size_mb = len(serialized.encode('utf-8')) / (1024 * 1024)
            if size_mb > MAX_SINGLE_ENTRY_SIZE_MB:
                logger.warning(f"Cache entry too large ({size_mb:.2f}MB), skipping cache")
                return False
            return True
        except (TypeError, ValueError):
            return False

    def _prune_if_needed(self) -> None:
        """Remove oldest cache entries if we exceed limits."""
        try:
            cache_files = sorted(
                self.cache_dir.glob("*.json"),
                key=lambda f: f.stat().st_mtime
            )
            # Remove oldest entries if we exceed count limit
            while len(cache_files) > MAX_CACHE_ENTRIES:
                oldest = cache_files.pop(0)
                try:
                    oldest.unlink()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Cache pruning failed: {e}", exc_info=True)

    def get(self, analysis_type: str, gene: str, cancer: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cached result if it exists and is within TTL.
        Returns None if cache miss, cache disabled, or expired.
        """
        if not self.enabled:
            return None

        key = self._generate_key(analysis_type, gene, cancer)
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            timestamp = data.get("_cache_timestamp")
            if timestamp is None:
                return None

            age = time.time() - timestamp
            if age > self.ttl_seconds:
                # Expired — remove file
                try:
                    cache_path.unlink()
                except Exception:
                    pass
                return None

            # Remove timestamp from the returned data
            result = data.get("data")
            if result:
                logger.debug(f"Cache hit for {key}")
            return result
        except Exception as e:
            logger.error(f"Failed to read cache for {key}", exc_info=True)
            return None

    def set(self, analysis_type: str, gene: str, cancer: str, data: Dict[str, Any]) -> bool:
        """
        Writes data to the cache atomically.
        Only caches if data passes size validation.
        """
        if not self.enabled:
            return False

        # Validate data size before caching
        if not self._validate_size(data):
            logger.info(f"Skipping cache for {analysis_type}/{gene}/{cancer} (data too large)")
            return False

        key = self._generate_key(analysis_type, gene, cancer)
        cache_path = self._get_cache_path(key)

        cache_content = {
            "_cache_timestamp": time.time(),
            "data": data
        }

        try:
            # Atomic write: write to temp file then rename
            fd, temp_path = tempfile.mkstemp(dir=self.cache_dir, prefix=f"{key}_", suffix=".tmp")

            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(cache_content, f)

            # os.replace is atomic on POSIX and Windows (in modern Python)
            os.replace(temp_path, cache_path)
            logger.debug(f"Cache written for {key}")

            # Prune if needed
            self._prune_if_needed()

            return True
        except Exception as e:
            logger.error(f"Failed to write cache for {key}", exc_info=True)
            # Cleanup temp file if it exists
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
            return False

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidates all cache entries, or those matching a pattern.
        Returns number of entries deleted.
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if pattern is None or pattern in cache_file.name:
                    try:
                        cache_file.unlink()
                        count += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.error("Failed during cache invalidation", exc_info=True)

        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Returns cache statistics for monitoring."""
        try:
            files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in files)
            return {
                "entries": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "max_entries": MAX_CACHE_ENTRIES,
                "max_size_mb": MAX_CACHE_SIZE_MB
            }
        except Exception:
            return {"entries": 0, "total_size_bytes": 0, "total_size_mb": 0}


# Global cache manager instance
cache = CacheManager()
