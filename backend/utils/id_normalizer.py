import re
from typing import Optional
from backend.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)

# Cache of already-warned IDs to avoid log flooding
_warned_ids: set = set()


def normalize_tcga_id(sample_id: str) -> Optional[str]:
    """
    Normalizes a sample ID to a stable patient identifier.

    Handles two formats:
    1. Standard TCGA barcodes: 'TCGA-A8-A06X-01A-...'  -> 'TCGA-A8-A06X'
    2. cBioPortal-style IDs:   'LUAD-NYU847'            -> 'LUAD-NYU847'
                                'LUAD-5O6B5-Normal'      -> 'LUAD-5O6B5'

    Returns None if the ID is empty or clearly malformed.
    """
    if not sample_id or not isinstance(sample_id, str):
        return None

    sample_id = sample_id.strip()
    if not sample_id:
        return None

    # --- Pattern 1: Standard TCGA barcode (TCGA-AB-1234-...) ---
    match = re.match(r'^(TCGA-[A-Z0-9]{2}-[A-Z0-9]{4})', sample_id, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # --- Pattern 2: cBioPortal cancer-type prefix (hyphen or underscore separator) ---
    # Handles: LUAD-NYU847, LUAD-RT-S01818, BRCA-A1B2C3, LUAD_E00565
    cbio_match = re.match(
        r'^([A-Z]{2,6})[-_]([A-Z0-9]{1,3}[-_])?([A-Z0-9]{3,})(?:[-_](?:Normal|Tumor|\d{2}[A-Z]?).*)?$',
        sample_id,
        re.IGNORECASE
    )
    if cbio_match:
        cancer_code = cbio_match.group(1).upper()
        mid = (cbio_match.group(2) or "").strip("-_").upper()
        patient_token = cbio_match.group(3).upper()
        if mid:
            return f"{cancer_code}-{mid}-{patient_token}"
        return f"{cancer_code}-{patient_token}"

    # --- Unknown format: warn only once per unique ID ---
    if sample_id not in _warned_ids:
        _warned_ids.add(sample_id)
        logger.warning(f"Could not normalize sample ID to known format: {sample_id!r}")
    return None
