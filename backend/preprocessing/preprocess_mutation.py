import pandas as pd
import json
from pathlib import Path
from backend.config import (
    RAW_MUTATION_DIR, 
    PROCESSED_MUTATION_DIR, 
    SUPPORTED_CANCERS
)
from backend.utils.logger import StructuredLogger
from backend.utils.id_normalizer import normalize_tcga_id

logger = StructuredLogger(__name__)

def is_processed() -> bool:
    for cancer in SUPPORTED_CANCERS.values():
        if not (PROCESSED_MUTATION_DIR / f"{cancer.lower()}_mutations.parquet").exists():
            return False
    if not (PROCESSED_MUTATION_DIR / "cohort_sizes.json").exists():
        return False
    return True

def standardize_mutation_type(variant_class: str) -> str:
    if pd.isna(variant_class):
        return "Other"
        
    v = str(variant_class).strip().lower()
    
    if "missense" in v:
        return "Missense"
    elif "nonsense" in v:
        return "Nonsense"
    elif "frame_shift" in v or "frameshift" in v:
        return "Frameshift"
    elif "splice" in v:
        return "Splice Site"
    elif "in_frame" in v or "inframe" in v:
        return "In-frame Indel"
    elif "silent" in v:
        return "Silent"
    else:
        return "Other"

def preprocess_mutation(force: bool = False):
    if is_processed() and not force:
        logger.info("Mutation data already processed. Skipping.")
        return

    logger.info("Starting mutation preprocessing")
    PROCESSED_MUTATION_DIR.mkdir(parents=True, exist_ok=True)
    
    cohort_sizes = {}
    
    for display_name, code in SUPPORTED_CANCERS.items():
        # Look for the corresponding MAF file
        maf_files = list(RAW_MUTATION_DIR.glob(f"*{code.lower()}*.txt")) + list(RAW_MUTATION_DIR.glob(f"*{code}*.txt"))
        if not maf_files:
            logger.warning(f"No mutation MAF file found for {code} in {RAW_MUTATION_DIR}")
            continue
            
        maf_path = maf_files[0]
        logger.info(f"Processing mutation data for {code}: {maf_path.name}")
        
        try:
            # Skip comment lines starting with #
            df = pd.read_csv(
                maf_path, 
                sep="\t", 
                comment='#',
                usecols=lambda c: c in ['Hugo_Symbol', 'Tumor_Sample_Barcode', 'Variant_Classification', 'Variant_Type'],
                dtype=str
            )
            
            # Step 2: Normalize sample IDs
            df['normalized_id'] = df['Tumor_Sample_Barcode'].apply(normalize_tcga_id)
            
            # Step 3: Standardize mutation classifications
            df['mutation_type'] = df['Variant_Classification'].apply(standardize_mutation_type)
            
            # Step 4: Compute cohort size
            # Number of unique normalized patients in the MAF
            valid_patients = df['normalized_id'].dropna().unique()
            cohort_size = len(valid_patients)
            cohort_sizes[code] = cohort_size
            
            logger.info(f"{code} cohort size: {cohort_size} unique patients")
            
            # Step 5: Save processed files
            # Keep only necessary columns
            final_df = df[['Hugo_Symbol', 'normalized_id', 'mutation_type', 'Variant_Type']].dropna(subset=['normalized_id'])
            final_df.to_parquet(PROCESSED_MUTATION_DIR / f"{code.lower()}_mutations.parquet")
            
        except Exception as e:
            logger.error(f"Error processing mutation data for {code}", exc_info=True)
            
    # Save cohort sizes
    with open(PROCESSED_MUTATION_DIR / "cohort_sizes.json", "w", encoding="utf-8") as f:
        json.dump(cohort_sizes, f, indent=2)
        
    logger.info("Mutation preprocessing completed")

if __name__ == "__main__":
    preprocess_mutation(force=True)
