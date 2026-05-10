import pandas as pd
import numpy as np
import json
from pathlib import Path

# Fix paths for test imports
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.config import DATA_DIR

def create_fixtures():
    np.random.seed(42)
    
    # We will override the config paths in tests, but let's place them in a specific fixture dir
    fixture_dir = Path(__file__).parent
    
    # Create expression fixtures
    genes = [f"GENE{i}" for i in range(1, 51)]
    genes.append("TP53") # Known gene
    
    tumor_samples = [f"TCGA-A8-A06{chr(65+i)}" for i in range(30)]
    normal_samples = [f"TCGA-A8-A06{chr(97+i)}" for i in range(15)]
    
    # Tumor expression data
    tumor_data = np.random.normal(5, 1, size=(len(genes), len(tumor_samples)))
    # Make TP53 highly expressed in tumor
    tp53_idx = genes.index("TP53")
    tumor_data[tp53_idx, :] = np.random.normal(8, 0.5, size=len(tumor_samples))
    
    tumor_df = pd.DataFrame(tumor_data, index=genes, columns=tumor_samples)
    tumor_df.index.name = "symbol"
    
    # Normal expression data
    normal_data = np.random.normal(4, 1, size=(len(genes), len(normal_samples)))
    # Make TP53 low in normal -> upregulated in tumor
    normal_data[tp53_idx, :] = np.random.normal(2, 0.5, size=len(normal_samples))
    
    normal_df = pd.DataFrame(normal_data, index=genes, columns=normal_samples)
    normal_df.index.name = "symbol"
    
    expr_dir = fixture_dir / "processed" / "expression"
    expr_dir.mkdir(parents=True, exist_ok=True)
    tumor_df.to_parquet(expr_dir / "brca_tumor.parquet")
    normal_df.to_parquet(expr_dir / "brca_normal.parquet")
    
    # Clinical fixture
    clinical_dir = fixture_dir / "processed" / "clinical"
    clinical_dir.mkdir(parents=True, exist_ok=True)
    
    # We need matching normalized IDs. Let's say all tumor samples are patients.
    normalized_ids = [s[:12] for s in tumor_samples] # "TCGA-A8-A06X" format usually, but here our samples are 12 chars: TCGA-A8-A06A
    # wait, normalize_tcga_id extracts TCGA-XX-XXXX (12 chars). "TCGA-A8-A06A" is 12 chars.
    
    survival_time = np.random.exponential(1000, size=len(normalized_ids))
    # Make TP53 high expression correlate with poor survival
    # high expr -> shorter survival
    tp53_expr = tumor_data[tp53_idx, :]
    median_expr = np.median(tp53_expr)
    for i in range(len(normalized_ids)):
        if tp53_expr[i] > median_expr:
            survival_time[i] = np.random.exponential(500) # Shorter
        else:
            survival_time[i] = np.random.exponential(1500) # Longer
            
    survival_event = np.random.binomial(1, 0.7, size=len(normalized_ids))
    
    clinical_df = pd.DataFrame({
        "normalized_id": normalized_ids,
        "survival_time": survival_time,
        "survival_event": survival_event
    })
    clinical_df.to_parquet(clinical_dir / "brca_survival.parquet")
    
    # Mutation fixture
    mutation_dir = fixture_dir / "processed" / "mutation"
    mutation_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some mutations
    mut_normalized_ids = np.random.choice(normalized_ids, size=20, replace=True)
    mut_genes = np.random.choice(genes, size=20, replace=True)
    mut_types = np.random.choice(["Missense", "Nonsense", "Frameshift", "Silent"], size=20, replace=True)
    
    # Ensure TP53 has mutations
    mut_normalized_ids = np.append(mut_normalized_ids, normalized_ids[:5])
    mut_genes = np.append(mut_genes, ["TP53"] * 5)
    mut_types = np.append(mut_types, ["Missense", "Missense", "Nonsense", "Frameshift", "Silent"])
    
    mut_df = pd.DataFrame({
        "Hugo_Symbol": mut_genes,
        "normalized_id": mut_normalized_ids,
        "mutation_type": mut_types,
        "Variant_Type": ["SNP"] * len(mut_genes)
    })
    mut_df.to_parquet(mutation_dir / "brca_mutations.parquet")
    
    cohort_sizes = {"BRCA": len(normalized_ids)}
    with open(mutation_dir / "cohort_sizes.json", "w") as f:
        json.dump(cohort_sizes, f)
        
    print("Fixtures created successfully.")

if __name__ == "__main__":
    create_fixtures()
