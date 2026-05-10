import pandas as pd
import numpy as np
from pathlib import Path
import os
import gc
from backend.config import (
    RAW_EXPRESSION_DIR, 
    PROCESSED_EXPRESSION_DIR, 
    SUPPORTED_CANCERS, 
    HGNC_REFERENCE_FILE,
    MIN_TUMOR_SAMPLES,
    MIN_NORMAL_SAMPLES
)
from backend.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)

def is_processed() -> bool:
    """Checks if expression data is already processed and non-empty."""
    for cancer in SUPPORTED_CANCERS.values():
        tumor_path = PROCESSED_EXPRESSION_DIR / f"{cancer.lower()}_tumor.parquet"
        normal_path = PROCESSED_EXPRESSION_DIR / f"{cancer.lower()}_normal.parquet"
        if not tumor_path.exists() or not normal_path.exists():
            return False
    
    index_path = PROCESSED_EXPRESSION_DIR / "gene_index.txt"
    if not index_path.exists():
        return False
    
    # Crucial: ensure gene_index is not empty (a failed previous run may leave empty files)
    if index_path.stat().st_size == 0:
        return False
        
    return True

def load_hgnc_mapping() -> pd.DataFrame:
    """Loads mapping from Ensembl ID to HGNC Symbol from the HGNC TSV."""
    logger.info("Loading HGNC mapping")
    try:
        hgnc_df = pd.read_csv(HGNC_REFERENCE_FILE, sep="\t", dtype=str)
        
        symbol_col = "symbol" if "symbol" in hgnc_df.columns else "Approved symbol"
        ensembl_col = "ensembl_gene_id" if "ensembl_gene_id" in hgnc_df.columns else "Ensembl gene ID"
            
        if symbol_col in hgnc_df.columns and ensembl_col in hgnc_df.columns:
            mapping = hgnc_df[[symbol_col, ensembl_col]].dropna()
            mapping.columns = ["symbol", "ensembl_id"]
            return mapping
        else:
            logger.warning("Could not find standard HGNC columns. Proceeding without explicit HGNC mapping mapping.")
            return pd.DataFrame(columns=["symbol", "ensembl_id"])
    except Exception as e:
        logger.error("Failed to load HGNC mapping", exc_info=True)
        return pd.DataFrame(columns=["symbol", "ensembl_id"])

def preprocess_expression(force: bool = False):
    if is_processed() and not force:
        logger.info("Expression data already processed. Skipping.")
        return

    logger.info("Starting expression preprocessing")
    
    phenotype_path = RAW_EXPRESSION_DIR / "TcgaTargetGtex_phenotype.txt"
    expression_path = RAW_EXPRESSION_DIR / "TcgaTargetGtex_rsem_gene_tpm"
    
    # If the exact names are different, try to find them
    if not phenotype_path.exists():
        files = list(RAW_EXPRESSION_DIR.glob("*phenotype*"))
        if files:
            phenotype_path = files[0]
            
    if not expression_path.exists():
        files = list(RAW_EXPRESSION_DIR.glob("*rsem_gene_tpm*"))
        if files:
            expression_path = files[0]

    if not phenotype_path.exists() or not expression_path.exists():
        logger.error(f"Raw expression files not found in {RAW_EXPRESSION_DIR}")
        return

    # Step 1 & 2: Load and filter phenotype
    logger.info("Loading phenotype data")
    try:
        # Columns in Xena TCGA/GTEx phenotype file:
        # 'sample', 'detailed_category', 'primary disease or tissue',
        # '_primary_site', '_sample_type', '_gender', '_study'
        pheno_df = pd.read_csv(phenotype_path, sep="\t", dtype=str, encoding="latin1")
        logger.info(f"Phenotype columns: {list(pheno_df.columns)}")
        
        # Standardize column names — only assign each target once (first match wins)
        col_map = {}
        assigned_targets = set()
        
        # Priority-ordered detection rules: (condition_fn, target_name)
        def _make_rules():
            return [
                # Exact matches first
                (lambda c: c == "sample", "sample"),
                (lambda c: c == "_sample_type", "sample_type"),
                (lambda c: c == "primary disease or tissue", "primary_disease"),
                # Fuzzy fallbacks
                (lambda c: "sample" in c.lower() and "type" not in c.lower() and "id" not in c.lower(), "sample"),
                (lambda c: "sample_type" in c.lower() or ("type" in c.lower() and "sample" in c.lower()), "sample_type"),
                (lambda c: "disease" in c.lower() and "_primary_site" not in c, "primary_disease"),
            ]
        
        for col in pheno_df.columns:
            for condition, target in _make_rules():
                if target not in assigned_targets and condition(col):
                    col_map[col] = target
                    assigned_targets.add(target)
                    break
                
        logger.info(f"Phenotype column map: {col_map}")
        pheno_df.rename(columns=col_map, inplace=True)
        
        # Ensure we have the required columns
        req_cols = ["sample", "sample_type", "primary_disease"]
        for col in req_cols:
            if col not in pheno_df.columns:
                if col == "sample":
                    pheno_df.rename(columns={pheno_df.columns[0]: "sample"}, inplace=True)
                else:
                    logger.error(f"Missing required column '{col}' in phenotype data. Available: {list(pheno_df.columns)}")
                    return
    except Exception as e:
        logger.error("Error processing phenotype file", exc_info=True)
        return

    # Extract sample lists for BRCA, LUAD, COAD
    # We need TCGA Primary Tumor, TCGA Solid Tissue Normal, and GTEx normals
    cancer_samples = {cancer: {"tumor": [], "normal": []} for cancer in SUPPORTED_CANCERS.values()}
    
    for _, row in pheno_df.iterrows():
        sample = row.get("sample")
        # When duplicate column renames occur, row.get returns a Series — guard against it
        if hasattr(sample, '__iter__') and not isinstance(sample, str):
            sample = sample.iloc[0] if len(sample) > 0 else None
        sample_type_val = row.get("sample_type", "")
        if hasattr(sample_type_val, '__iter__') and not isinstance(sample_type_val, str):
            sample_type_val = sample_type_val.iloc[0] if len(sample_type_val) > 0 else ""
        disease_val = row.get("primary_disease", "")
        if hasattr(disease_val, '__iter__') and not isinstance(disease_val, str):
            disease_val = disease_val.iloc[0] if len(disease_val) > 0 else ""
            
        sample_type = str(sample_type_val).lower()
        disease = str(disease_val).lower()
        
        if pd.isna(sample) or not sample:
            continue
            
        # Determine cancer type match
        matched_cancer = None
        if "breast" in disease:
            matched_cancer = "BRCA"
        elif "lung" in disease and "adeno" in disease:
            matched_cancer = "LUAD"
        elif "colon" in disease:
            matched_cancer = "COAD"
            
        if matched_cancer:
            if "primary tumor" in sample_type or "primary solid tumor" in sample_type:
                cancer_samples[matched_cancer]["tumor"].append(sample)
            elif "solid tissue normal" in sample_type or "normal" in sample_type:
                cancer_samples[matched_cancer]["normal"].append(sample)

    all_relevant_samples = set()
    for c_data in cancer_samples.values():
        all_relevant_samples.update(c_data["tumor"])
        all_relevant_samples.update(c_data["normal"])
        
    logger.info(f"Identified {len(all_relevant_samples)} relevant samples across all cohorts")

    # Step 3: Load expression matrix in chunks
    logger.info("Processing expression matrix in chunks")
    
    # Get column names first to only load relevant columns
    try:
        import gzip
        if str(expression_path).endswith('.gz'):
            with gzip.open(expression_path, 'rt', encoding='latin1') as f:
                header = f.readline().strip().split('\t')
        else:
            with open(expression_path, 'r') as f:
                header = f.readline().strip().split('\t')
    except Exception as e:
        logger.error("Failed to read expression header", exc_info=True)
        return
        
    gene_col = header[0]
    relevant_cols = [col for col in header if col in all_relevant_samples]
    cols_to_use = [gene_col] + relevant_cols
    
    # If no relevant columns, abort
    if not relevant_cols:
        logger.error("No matching samples found in expression matrix")
        return

    chunk_size = 5000
    expr_chunks = []
    
    try:
        for chunk in pd.read_csv(expression_path, sep="\t", usecols=cols_to_use, chunksize=chunk_size):
            expr_chunks.append(chunk)
            # gc.collect() can be called but chunking should handle it mostly
    except Exception as e:
        logger.error("Error reading expression chunks", exc_info=True)
        return
        
    expr_df = pd.concat(expr_chunks, ignore_index=True)
    del expr_chunks
    gc.collect()

    # Step 4: Convert Ensembl IDs to HGNC
    mapping = load_hgnc_mapping()
    
    # The gene_col often contains version numbers: ENSG00000141510.11
    # Strip versions
    expr_df["ensembl_id_base"] = expr_df[gene_col].str.split('.').str[0]
    
    if not mapping.empty:
        # Merge with mapping
        expr_df = expr_df.merge(mapping, left_on="ensembl_id_base", right_on="ensembl_id", how="inner")
        
        # If multiple Ensembl IDs map to the same symbol, keep the one with highest mean
        # First calculate row means for numeric columns
        numeric_cols = expr_df.select_dtypes(include=[np.number]).columns
        expr_df['mean_expr'] = expr_df[numeric_cols].mean(axis=1)
        
        # Sort by symbol and mean expr, drop duplicates keeping highest
        expr_df = expr_df.sort_values(by=["symbol", "mean_expr"], ascending=[True, False])
        expr_df = expr_df.drop_duplicates(subset=["symbol"], keep="first")
        
        # Set index to symbol
        expr_df.set_index("symbol", inplace=True)
    else:
        # If no mapping, just use whatever is in the ID column (sometimes they are already symbols)
        # Or just use the base Ensembl ID as a fallback to allow the system to run
        expr_df.set_index("ensembl_id_base", inplace=True)
        expr_df.index.name = "symbol"
        
    # Drop helper columns
    cols_to_drop = [c for c in [gene_col, "ensembl_id", "mean_expr"] if c in expr_df.columns]
    expr_df.drop(columns=cols_to_drop, inplace=True, errors="ignore")

    # Step 5 & 6: Separate and Save
    PROCESSED_EXPRESSION_DIR.mkdir(parents=True, exist_ok=True)
    
    all_genes = set(expr_df.index)
    
    for cancer_code, sample_dict in cancer_samples.items():
        tumor_samples = [s for s in sample_dict["tumor"] if s in expr_df.columns]
        normal_samples = [s for s in sample_dict["normal"] if s in expr_df.columns]
        
        if len(tumor_samples) < MIN_TUMOR_SAMPLES:
            logger.warning(f"{cancer_code} has only {len(tumor_samples)} tumor samples (min {MIN_TUMOR_SAMPLES})")
        if len(normal_samples) < MIN_NORMAL_SAMPLES:
            logger.warning(f"{cancer_code} has only {len(normal_samples)} normal samples (min {MIN_NORMAL_SAMPLES})")
            
        logger.info(f"{cancer_code}: {len(tumor_samples)} tumor, {len(normal_samples)} normal")
            
        tumor_df = expr_df[tumor_samples]
        normal_df = expr_df[normal_samples]
        
        tumor_df.to_parquet(PROCESSED_EXPRESSION_DIR / f"{cancer_code.lower()}_tumor.parquet")
        normal_df.to_parquet(PROCESSED_EXPRESSION_DIR / f"{cancer_code.lower()}_normal.parquet")

    # Step 7: Save gene index
    with open(PROCESSED_EXPRESSION_DIR / "gene_index.txt", "w") as f:
        for gene in sorted(list(all_genes)):
            f.write(f"{gene}\n")
            
    logger.info("Expression preprocessing completed")

if __name__ == "__main__":
    preprocess_expression(force=True)
