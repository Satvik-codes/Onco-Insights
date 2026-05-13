"""
Memory utility functions for low-memory execution on constrained cloud instances.

Designed to work on both Linux (Render) and Windows (local dev/testing).
"""
import gc
import logging
import os
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# Memory budget for the analysis pipeline (in bytes)
# 512 MB total, leave ~128 MB headroom for Python runtime, plotly, etc.
MEMORY_BUDGET_BYTES = 384 * 1024 * 1024  # 384 MB usable for data

# --- Platform-aware memory tracking ---
try:
    import resource
    _HAS_RESOURCE = True
except ImportError:
    _HAS_RESOURCE = False

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


def get_memory_usage_mb() -> float:
    """Returns peak process RSS memory usage in MB (ru_maxrss on Linux)."""
    if _HAS_RESOURCE:
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in kilobytes on Linux
            return usage.ru_maxrss / 1024
        except Exception:
            pass
    return 0.0


def get_memory_usage_current_mb() -> float:
    """
    Returns current memory usage in MB.
    Uses /proc/self/status on Linux, psutil as fallback, or 0 on unsupported platforms.
    """
    # Try /proc/self/status first (most accurate on Linux)
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    # VmRSS is in kB
                    return int(line.split()[1]) / 1024
    except Exception:
        pass

    # Fallback to psutil
    if _HAS_PSUTIL:
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            return mem_info.rss / (1024 * 1024)
        except Exception:
            pass

    # Last resort: resource module peak
    return get_memory_usage_mb()


def log_memory(tag: str = "") -> None:
    """Log current memory usage with an optional tag."""
    current_mb = get_memory_usage_current_mb()
    peak_mb = get_memory_usage_mb()
    logger.info(
        f"[MEMORY] {tag} | current={current_mb:.1f}MB peak={peak_mb:.1f}MB"
    )


def check_memory_budget(tag: str = "") -> bool:
    """
    Check if we're within the memory budget.
    Returns True if within budget, False if over.
    """
    current = get_memory_usage_current_mb() * 1024 * 1024
    if current > MEMORY_BUDGET_BYTES:
        logger.warning(
            f"[MEMORY] Budget exceeded {tag}: {current / (1024*1024):.1f}MB > {MEMORY_BUDGET_BYTES / (1024*1024):.1f}MB"
        )
        return False
    return True


def force_gc() -> None:
    """Force garbage collection and return memory to the OS where possible."""
    gc.collect()


def downcast_float64_to_float32(df):
    """Downcast float64 columns to float32 in-place to save memory."""
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = df[col].astype("float32")
    return df


def downcast_int64_to_int32(df):
    """Downcast int64 columns to int32 in-place to save memory."""
    for col in df.select_dtypes(include=["int64"]).columns:
        # Check if values fit in int32 range
        if df[col].isna().all():
            df[col] = df[col].astype("Int32")
        elif df[col].min() >= -2_147_483_648 and df[col].max() <= 2_147_483_647:
            df[col] = df[col].astype("int32")
    return df


def downcast_numeric(df):
    """Downcast all numeric columns to save memory."""
    df = downcast_float64_to_float32(df)
    df = downcast_int64_to_int32(df)
    return df


def safe_delete(obj, attr_name: str = None):
    """
    Delete an object reference and free memory.
    If attr_name is provided, deletes the attribute from the object.
    """
    try:
        if attr_name:
            delattr(obj, attr_name)
        else:
            del obj
    except Exception:
        pass
    gc.collect()