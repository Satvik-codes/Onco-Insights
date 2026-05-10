import os
from pathlib import Path
import pandas as pd
import numpy as np
import json
import sys

# Ensure backend can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import (
    PROCESSED_EXPRESSION_DIR,
    PROCESSED_CLINICAL_DIR,
    PROCESSED_MUTATION_DIR,
    SUPPORTED_CANCERS
)

def generate_mock_data():
    PROCESSED_EXPRESSION_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_CLINICAL_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_MUTATION_DIR.mkdir(parents=True, exist_ok=True)
    
    # Common cancer genes to populate
    genes = ["BRCA1", "TP53", "EGFR", "PTEN", "KRAS", "APC", "PIK3CA", "RB1", "CDH1", "SMAD4"]
    
    # Write gene index
    with open(PROCESSED_EXPRESSION_DIR / "gene_index.txt", "w") as f:
        for g in sorted(genes):
            f.write(f"{g}\n")
            
    # Write empty HGNC mapping file (to prevent loading error)
    hgnc_dir = Path(__file__).parent / "data" / "raw"
    hgnc_dir.mkdir(parents=True, exist_ok=True)
    with open(hgnc_dir / "hgnc_approved_symbols.txt", "w") as f:
        f.write("Approved symbol\tEnsembl gene ID\n")
        for g in genes:
            f.write(f"{g}\tENSG00000000000\n")
            
    cohort_sizes = {}

    for name, code in SUPPORTED_CANCERS.items():
        # Create some samples
        tumor_samples = [f"TCGA-{code}-TUMOR-{i:03d}" for i in range(1, 61)]  # 60 tumor
        normal_samples = [f"TCGA-{code}-NORMAL-{i:03d}" for i in range(1, 16)] # 15 normal
        
        # 1. Expression Parquets
        # Index = symbol, Columns = samples
        tumor_expr = pd.DataFrame(
            np.random.lognormal(mean=2, sigma=1, size=(len(genes), len(tumor_samples))),
            index=genes,
            columns=tumor_samples
        )
        # Give normal lower expression on average to show DE
        normal_expr = pd.DataFrame(
            np.random.lognormal(mean=1, sigma=0.5, size=(len(genes), len(normal_samples))),
            index=genes,
            columns=normal_samples
        )
        
        tumor_expr.index.name = "symbol"
        normal_expr.index.name = "symbol"
        
        tumor_expr.to_parquet(PROCESSED_EXPRESSION_DIR / f"{code.lower()}_tumor.parquet")
        normal_expr.to_parquet(PROCESSED_EXPRESSION_DIR / f"{code.lower()}_normal.parquet")
        
        # 2. Clinical (Survival) Parquets
        # Columns: normalized_id, survival_time, survival_event
        clinical_df = pd.DataFrame({
            "normalized_id": tumor_samples,
            "survival_time": np.random.randint(30, 3000, size=len(tumor_samples)),
            "survival_event": np.random.choice([0.0, 1.0], size=len(tumor_samples), p=[0.4, 0.6])
        })
        clinical_df.to_parquet(PROCESSED_CLINICAL_DIR / f"{code.lower()}_survival.parquet")
        
        # 3. Mutation Parquets
        # Columns: Hugo_Symbol, normalized_id, mutation_type, Variant_Type
        mutations = []
        for g in genes:
            # 10% mutation rate
            mutated_samples = np.random.choice(tumor_samples, size=int(0.1 * len(tumor_samples)), replace=False)
            for s in mutated_samples:
                mutations.append({
                    "Hugo_Symbol": g,
                    "normalized_id": s,
                    "mutation_type": np.random.choice(["Missense", "Nonsense", "Frameshift"]),
                    "Variant_Type": "SNP"
                })
        mut_df = pd.DataFrame(mutations)
        if mut_df.empty: # Edge case
            mut_df = pd.DataFrame(columns=["Hugo_Symbol", "normalized_id", "mutation_type", "Variant_Type"])
        mut_df.to_parquet(PROCESSED_MUTATION_DIR / f"{code.lower()}_mutations.parquet")
        
        cohort_sizes[code] = len(tumor_samples)

    # Save cohort sizes
    with open(PROCESSED_MUTATION_DIR / "cohort_sizes.json", "w") as f:
        json.dump(cohort_sizes, f)
        
    print("Mock data generated successfully! You can now run the app.")

if __name__ == "__main__":
    generate_mock_data()
