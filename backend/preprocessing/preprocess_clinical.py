import pandas as pd
import numpy as np
from pathlib import Path
from backend.config import (
    RAW_CLINICAL_DIR, 
    PROCESSED_CLINICAL_DIR, 
    SUPPORTED_CANCERS
)
from backend.utils.logger import StructuredLogger
from backend.utils.id_normalizer import normalize_tcga_id

logger = StructuredLogger(__name__)

def is_processed() -> bool:
    for cancer in SUPPORTED_CANCERS.values():
        if not (PROCESSED_CLINICAL_DIR / f"{cancer.lower()}_survival.parquet").exists():
            return False
    return True

def parse_survival_event(val) -> float:
    if pd.isna(val):
        return np.nan
        
    val_str = str(val).strip().upper()
    
    # Handle cBioPortal prefix format: "0:LIVING", "1:DECEASED", "0:CENSORED", etc.
    if ":" in val_str:
        prefix = val_str.split(":")[0].strip()
        if prefix == "1":
            return 1.0
        elif prefix == "0":
            return 0.0
    
    if val_str in ["1", "1.0", "1:DECEASED", "DECEASED", "TRUE", "DEAD"]:
        return 1.0
    elif val_str in ["0", "0.0", "0:LIVING", "LIVING", "FALSE", "ALIVE"]:
        return 0.0
    
    return np.nan

def preprocess_clinical(force: bool = False):
    if is_processed() and not force:
        logger.info("Clinical data already processed. Skipping.")
        return

    logger.info("Starting clinical preprocessing")
    
    clinical_files = list(RAW_CLINICAL_DIR.glob("*.txt")) + list(RAW_CLINICAL_DIR.glob("*.tsv")) + list(RAW_CLINICAL_DIR.glob("*.csv"))
    if not clinical_files:
        logger.error(f"No clinical files found in {RAW_CLINICAL_DIR}")
        return
        
    # Assume first file is the Pan-Cancer or combined clinical file
    clinical_path = clinical_files[0]
    
    try:
        sep = "," if clinical_path.suffix == ".csv" else "\t"
        df = pd.read_csv(clinical_path, sep=sep, dtype=str)
    except Exception as e:
        logger.error("Failed to read clinical file", exc_info=True)
        return
        
    # Identify columns — support both TCGA pan-cancer and study-specific file layouts
    sample_col = None
    cancer_col = None
    os_time_col = None
    os_status_col = None

    # Priority exact-match candidates for key columns
    SAMPLE_EXACT = {"sample", "sample id", "patient id"}
    CANCER_EXACT = {"cancer type abbreviation", "tcga pancanatlas cancer type acronym"}
    TIME_EXACT   = {"os.time", "os_time", "overall survival (months)", "overall_survival_time_in_days", "survival_time"}
    STATUS_EXACT = {"os", "os_status", "overall survival status", "vital_status", "survival_status"}

    for col in df.columns:
        lower_col = col.lower().strip()
        if not sample_col and lower_col in SAMPLE_EXACT:
            sample_col = col
        if not cancer_col and lower_col in CANCER_EXACT:
            cancer_col = col
        if not os_time_col and lower_col in TIME_EXACT:
            os_time_col = col
        if not os_status_col and lower_col in STATUS_EXACT:
            os_status_col = col

    # Fuzzy fallbacks (only if exact match failed)
    for col in df.columns:
        lower_col = col.lower().strip()
        if not sample_col and ("sample" in lower_col or "patient" in lower_col):
            sample_col = col
        if not cancer_col and ("cancer" in lower_col or "abbreviation" in lower_col or "project" in lower_col):
            cancer_col = col
        if not os_time_col and ("os.time" in lower_col or "os_time" in lower_col or "survival" in lower_col and "time" in lower_col):
            os_time_col = col
        if not os_status_col and ("vital" in lower_col or "os_status" in lower_col or "survival status" in lower_col):
            os_status_col = col

    if not sample_col:
        sample_col = df.columns[0]  # last-resort fallback

    if not all([sample_col, os_time_col, os_status_col]):
        logger.error(f"Could not identify required columns. Found: sample={sample_col}, time={os_time_col}, status={os_status_col}")
        logger.error(f"Available columns: {list(df.columns)}")
        return
        
    # Step 2: Standardize sample IDs
    df['normalized_id'] = df[sample_col].apply(normalize_tcga_id)
    
    # Step 3: Convert survival event status to binary
    df['survival_event'] = df[os_status_col].apply(parse_survival_event)
    
    # Process survival time
    df['survival_time'] = pd.to_numeric(df[os_time_col], errors='coerce')
    
    # Step 4: Remove invalid rows
    initial_count = len(df)
    
    df = df.dropna(subset=['normalized_id', 'survival_time', 'survival_event'])
    df = df[df['survival_time'] > 0]
    
    removed = initial_count - len(df)
    logger.info(f"Removed {removed} rows due to invalid or missing data")
    
    # Step 5: Separate by cancer type
    PROCESSED_CLINICAL_DIR.mkdir(parents=True, exist_ok=True)
    
    if cancer_col:
        for display_name, code in SUPPORTED_CANCERS.items():
            # Try to match by code or name
            cancer_df = df[df[cancer_col].str.contains(code, case=False, na=False) | 
                           df[cancer_col].str.contains(display_name.split()[0], case=False, na=False)]
            
            if not cancer_df.empty:
                final_df = cancer_df[['normalized_id', 'survival_time', 'survival_event']]
                final_df.to_parquet(PROCESSED_CLINICAL_DIR / f"{code.lower()}_survival.parquet")
                logger.info(f"Saved {len(final_df)} clinical records for {code}")
            else:
                logger.warning(f"No clinical records found for {code}")
    else:
        # If no cancer column, we might need to rely on the file name or just save for all
        logger.warning("No cancer type column found. Saving all data to each supported cancer (assuming separated input later or single cohort)")
        final_df = df[['normalized_id', 'survival_time', 'survival_event']]
        for code in SUPPORTED_CANCERS.values():
            final_df.to_parquet(PROCESSED_CLINICAL_DIR / f"{code.lower()}_survival.parquet")

if __name__ == "__main__":
    preprocess_clinical(force=True)
