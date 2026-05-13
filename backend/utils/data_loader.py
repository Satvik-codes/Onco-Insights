"""
Efficient on-demand data loader for cancer gene analysis.

This module provides lazy-loading, memory-efficient access to
processed parquet datasets. It never loads global DataFrames and
only reads the specific cancer type and columns needed for each request.
"""
import gc
import json
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import numpy as np

from backend.config import (
    PROCESSED_EXPRESSION_DIR,
    PROCESSED_CLINICAL_DIR,
    PROCESSED_MUTATION_DIR,
    SUPPORTED_CANCERS,
)
from backend.utils.logger import StructuredLogger
from backend.utils.memory import log_memory, downcast_numeric, force_gc

logger = StructuredLogger(__name__)


# ---------------------------------------------------------------------------
# Gene index (lightweight, loaded once at module level - just a set of strings)
# ---------------------------------------------------------------------------
_gene_index: Optional[set] = None


def _load_gene_index() -> set:
    """Load the gene index (a set of gene symbols) - only ~60k strings."""
    global _gene_index
    if _gene_index is not None:
        return _gene_index
    index_path = PROCESSED_EXPRESSION_DIR / "gene_index.txt"
    if index_path.exists():
        with open(index_path, "r") as f:
            _gene_index = {line.strip().upper() for line in f if line.strip()}
    else:
        _gene_index = set()
    logger.info(f"Gene index loaded: {len(_gene_index)} genes")
    return _gene_index


def get_gene_index() -> set:
    """Public accessor for the gene index set."""
    return _load_gene_index()


# ---------------------------------------------------------------------------
# Cohort sizes (lightweight JSON dict - loaded once)
# ---------------------------------------------------------------------------
_cohort_sizes: Optional[dict] = None


def _load_cohort_sizes() -> dict:
    """Load cohort sizes from JSON - tiny file."""
    global _cohort_sizes
    if _cohort_sizes is not None:
        return _cohort_sizes
    path = PROCESSED_MUTATION_DIR / "cohort_sizes.json"
    if path.exists():
        with open(path, "r") as f:
            _cohort_sizes = json.load(f)
    else:
        _cohort_sizes = {}
    return _cohort_sizes


def get_cohort_size(cancer: str) -> int:
    """Get cohort size for a cancer type."""
    sizes = _load_cohort_sizes()
    return sizes.get(cancer.upper(), 0)


# ---------------------------------------------------------------------------
# On-demand parquet loading - only the cancer type requested
# ---------------------------------------------------------------------------

def load_expression_series(cancer: str, gene: str, kind: str = "tumor") -> Optional[np.ndarray]:
    """
    Load a single gene's expression values as a numpy float32 array.
    Returns None if gene not found.
    kind: 'tumor' or 'normal'

    Memory note: reads the full parquet for the cancer type, extracts one
    gene row, then immediately frees the DataFrame. Peak memory ~ size of
    one parquet file.
    """
    cancer_lower = cancer.lower()
    filename = f"{cancer_lower}_{kind}.parquet"
    path = PROCESSED_EXPRESSION_DIR / filename

    if not path.exists():
        return None

    try:
        df = pd.read_parquet(path)
        if gene not in df.index:
            del df
            force_gc()
            return None
        arr = df.loc[gene].values.astype(np.float32)
        del df
        force_gc()
        return arr
    except Exception as e:
        logger.error(f"Failed to load expression {kind} for {gene} in {cancer}: {e}")
        return None


def load_expression_row_with_samples(cancer: str, gene: str, kind: str = "tumor") -> Optional[Tuple[np.ndarray, pd.Index]]:
    """
    Load a single gene's expression values AND the sample IDs (column names).
    Returns (values_array, sample_ids_index) or None if gene not found.

    This is used by survival analysis which needs sample IDs for merging.
    """
    cancer_lower = cancer.lower()
    filename = f"{cancer_lower}_{kind}.parquet"
    path = PROCESSED_EXPRESSION_DIR / filename

    if not path.exists():
        return None

    try:
        df = pd.read_parquet(path)
        if gene not in df.index:
            del df
            force_gc()
            return None
        arr = df.loc[gene].values.astype(np.float32)
        sample_ids = df.columns.copy()
        del df
        force_gc()
        return arr, sample_ids
    except Exception as e:
        logger.error(f"Failed to load expression {kind} for {gene} in {cancer}: {e}")
        return None


def load_expression_tumor(cancer: str, gene: Optional[str] = None) -> pd.DataFrame:
    """
    Load tumor expression data for a specific cancer type.
    If gene is provided, returns only that gene's row as a DataFrame.
    """
    cancer_lower = cancer.lower()
    path = PROCESSED_EXPRESSION_DIR / f"{cancer_lower}_tumor.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Expression tumor file not found: {path}")

    df = pd.read_parquet(path)
    if gene:
        if gene in df.index:
            result = df.loc[[gene]].copy()
        else:
            result = pd.DataFrame()
        del df
        force_gc()
        return result
    return df


def load_expression_normal(cancer: str, gene: Optional[str] = None) -> pd.DataFrame:
    """
    Load normal expression data for a specific cancer type.
    If gene is provided, returns only that gene's row as a DataFrame.
    """
    cancer_lower = cancer.lower()
    path = PROCESSED_EXPRESSION_DIR / f"{cancer_lower}_normal.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Expression normal file not found: {path}")

    df = pd.read_parquet(path)
    if gene:
        if gene in df.index:
            result = df.loc[[gene]].copy()
        else:
            result = pd.DataFrame()
        del df
        force_gc()
        return result
    return df


def load_clinical(cancer: str) -> pd.DataFrame:
    """Load clinical/survival data for a specific cancer type."""
    cancer_lower = cancer.lower()
    path = PROCESSED_CLINICAL_DIR / f"{cancer_lower}_survival.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Clinical file not found: {path}")
    df = pd.read_parquet(path)
    return downcast_numeric(df)


def load_mutations(cancer: str, gene: Optional[str] = None) -> pd.DataFrame:
    """
    Load mutation data for a specific cancer type.
    If gene is provided, filters in-memory to reduce peak usage.
    """
    cancer_lower = cancer.lower()
    path = PROCESSED_MUTATION_DIR / f"{cancer_lower}_mutations.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Mutation file not found: {path}")

    df = pd.read_parquet(path)
    if gene:
        gene_df = df[df["Hugo_Symbol"] == gene].copy()
        del df
        force_gc()
        return gene_df
    return df


# ---------------------------------------------------------------------------
# Memory-safe combined loaders
# ---------------------------------------------------------------------------

def load_survival_inputs(cancer: str, gene: str) -> tuple:
    """
    Load expression series + clinical data for survival analysis.
    Returns (gene_expr_array, sample_ids, clinical_df) or raises.
    """
    result = load_expression_row_with_samples(cancer, gene, kind="tumor")
    if result is None:
        raise ValueError(f"Gene '{gene}' not found in expression data for {cancer}")

    expr_arr, sample_ids = result
    clinical_df = load_clinical(cancer)
    return expr_arr, sample_ids, clinical_df


def cleanup_dataframe(df: pd.DataFrame) -> None:
    """Explicitly delete a DataFrame and force GC."""
    if df is not None:
        try:
            del df
        except Exception:
            pass
        force_gc()


def cleanup_arrays(*arrays) -> None:
    """Delete numpy arrays and force GC."""
    for arr in arrays:
        if arr is not None:
            try:
                del arr
            except Exception:
                pass
    force_gc()