import os
from typing import Tuple, Dict, Any, List
from backend.config import HGNC_REFERENCE_FILE, PROCESSED_EXPRESSION_DIR, SUPPORTED_CANCERS
from backend.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)

# ---------------------------------------------------------------------------
# HGNC symbols — loaded once at module level (small file, ~30k strings)
# ---------------------------------------------------------------------------
def load_hgnc_symbols() -> set:
    symbols = set()
    try:
        if HGNC_REFERENCE_FILE.exists():
            with open(HGNC_REFERENCE_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) > 1:
                        symbol = parts[1].upper()
                        if symbol and symbol != "SYMBOL":
                            symbols.add(symbol)
    except Exception as e:
        logger.error("Failed to load HGNC reference file.", exc_info=True)
    return symbols


HGNC_SYMBOLS = load_hgnc_symbols()


# ---------------------------------------------------------------------------
# Processed genes — LAZY LOADING (not at module import time)
# The gene index file is only read when first needed, not at startup.
# Exposed as PROCESSED_GENES (public) for backward compatibility with tests.
# ---------------------------------------------------------------------------
_genes_loaded = False
PROCESSED_GENES: set = set()


def _load_processed_genes() -> set:
    """Lazy-load the processed gene set only on first access."""
    global _genes_loaded, PROCESSED_GENES
    if _genes_loaded:
        return PROCESSED_GENES
    genes = set()
    index_file = PROCESSED_EXPRESSION_DIR / "gene_index.txt"
    try:
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                for line in f:
                    gene = line.strip().upper()
                    if gene:
                        genes.add(gene)
    except Exception as e:
        logger.error("Failed to load gene index file.", exc_info=True)
    PROCESSED_GENES = genes
    _genes_loaded = True
    logger.info(f"Processed gene index loaded: {len(genes)} genes")
    return genes


def get_processed_genes() -> set:
    """Public accessor — triggers lazy load on first call."""
    return _load_processed_genes()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def validate_gene(symbol: str) -> Tuple[bool, str, str]:
    """
    Validates a gene symbol.
    Returns: (is_valid, normalized_symbol, error_message)
    """
    if not symbol or not isinstance(symbol, str):
        return False, "", "Gene symbol must be a non-empty string."

    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        return False, "", "Gene symbol cannot be blank."

    if normalized_symbol not in HGNC_SYMBOLS:
        if HGNC_SYMBOLS:
            return False, normalized_symbol, f"Gene symbol '{normalized_symbol}' is not a valid HGNC approved symbol."

    if normalized_symbol not in get_processed_genes():
        if get_processed_genes():
            return False, normalized_symbol, f"Gene symbol '{normalized_symbol}' is not present in the processed dataset."

    return True, normalized_symbol, ""


def validate_cancer(cancer: str) -> Tuple[bool, str, str]:
    """
    Validates a cancer type.
    Returns: (is_valid, normalized_cancer, error_message)
    """
    if not cancer or not isinstance(cancer, str):
        return False, "", "Cancer type must be a non-empty string."

    normalized_cancer = cancer.strip().upper()

    if normalized_cancer in SUPPORTED_CANCERS.values():
        return True, normalized_cancer, ""

    for display_name, code in SUPPORTED_CANCERS.items():
        if display_name.upper() == normalized_cancer:
            return True, code, ""

    supported_list = ", ".join(SUPPORTED_CANCERS.values())
    return False, normalized_cancer, f"Cancer type '{cancer}' is not supported. Supported types: {supported_list}."


def validate_analysis_request(gene: str, cancer: str) -> Tuple[bool, str, str, List[Dict[str, str]]]:
    """
    Validates a complete analysis request.
    Returns: (is_valid, normalized_gene, normalized_cancer, errors)
    where errors is a list of dicts like {"field": "gene", "message": "error"}
    """
    errors = []

    is_gene_valid, norm_gene, gene_err = validate_gene(gene)
    if not is_gene_valid:
        errors.append({"field": "gene", "message": gene_err})

    is_cancer_valid, norm_cancer, cancer_err = validate_cancer(cancer)
    if not is_cancer_valid:
        errors.append({"field": "cancer", "message": cancer_err})

    is_valid = len(errors) == 0
    return is_valid, norm_gene, norm_cancer, errors
