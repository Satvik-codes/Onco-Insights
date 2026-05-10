import gzip, pandas as pd

# Simulate what preprocess_expression does
with gzip.open('backend/data/raw/expression/TcgaTargetGTEX_phenotype.txt.gz', 'rt', encoding='latin1') as f:
    pheno_df = pd.read_csv(f, sep='\t', dtype=str)

col_map = {}
for col in pheno_df.columns:
    lower_col = col.lower()
    if 'sample' in lower_col and 'type' not in lower_col and 'id' not in lower_col:
        col_map[col] = 'sample'
    elif 'type' in lower_col or 'sample_type' in lower_col:
        col_map[col] = 'sample_type'
    elif 'disease' in lower_col or 'primary' in lower_col or 'tissue' in lower_col:
        col_map[col] = 'primary_disease'
        
print('col_map:', col_map)
pheno_df.rename(columns=col_map, inplace=True)
print('Resulting cols:', list(pheno_df.columns))

# Check sample_type unique values
print('sample_type unique:', pheno_df['sample_type'].unique())
cancer_samples = {'BRCA': {'tumor': [], 'normal': []}, 'LUAD': {'tumor': [], 'normal': []}, 'COAD': {'tumor': [], 'normal': []}}

for _, row in pheno_df.iterrows():
    sample = row.get('sample')
    sample_type = str(row.get('sample_type', '')).lower()
    disease = str(row.get('primary_disease', '')).lower()
    if pd.isna(sample) or not sample:
        continue
    matched_cancer = None
    if 'breast' in disease:
        matched_cancer = 'BRCA'
    elif 'lung' in disease and 'adeno' in disease:
        matched_cancer = 'LUAD'
    elif 'colon' in disease:
        matched_cancer = 'COAD'
    if matched_cancer:
        if 'primary tumor' in sample_type or 'primary solid tumor' in sample_type:
            cancer_samples[matched_cancer]['tumor'].append(sample)
        elif 'solid tissue normal' in sample_type or 'normal' in sample_type:
            cancer_samples[matched_cancer]['normal'].append(sample)

for k, v in cancer_samples.items():
    print(f"{k}: {len(v['tumor'])} tumor, {len(v['normal'])} normal")
