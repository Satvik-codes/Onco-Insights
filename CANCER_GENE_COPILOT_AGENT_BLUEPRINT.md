# Cancer Gene Validation Copilot — AI Agent Implementation Blueprint

> **Instructions for the AI Agent:**
> This document is your complete implementation guide. You will read it top to bottom, execute every phase in order, and never skip a phase. Each phase has a checklist. You do not move to the next phase until every item in the current phase checklist is fully implemented, tested, and working. If you encounter an ambiguity, resolve it using the rules in Section 0 before continuing. The goal is a fully finished, production-ready backend — not a prototype.

---

## Section 0 — Global Rules (Read First, Apply Always)

These rules govern every decision you make throughout this project. They override any shortcut or simplification you might consider.

**Rule: No placeholders, ever.**
Every function, route, module, and utility must be fully implemented. Do not write `# TODO`, `pass`, or stub functions. If a module depends on a file that does not yet exist, create that file before writing the module.

**Rule: Fail loudly and informatively.**
Every module must raise specific, descriptive exceptions — never silent failures. Log the exact reason for failure, the input that caused it, and the module it came from. A researcher should be able to read the log and understand exactly what went wrong without reading source code.

**Rule: Strict separation of concerns.**
Data loading, preprocessing, statistical analysis, visualization, and AI interpretation are always separate layers. No analysis function should load raw files. No route handler should perform statistics. Enforce these boundaries throughout.

**Rule: All datasets are local.**
You will never call external APIs, scrape live websites, or fetch data at runtime. All TCGA, GTEx, and cBioPortal data is predownloaded and stored in the local `backend/data/` directory tree. Preprocessing scripts convert raw data into clean, analysis-ready files stored in `backend/data/processed/`. Analysis modules only ever read from processed files.

**Rule: Scientific validity is non-negotiable.**
Every statistical output must include sample counts, p-values, and the name of the statistical test used. Every visualization must show axis labels, sample counts, and significance markers. No result is returned to the frontend without these components.

**Rule: All configuration lives in one place.**
All file paths, model names, thresholds, API keys, and environment-specific values live in `backend/config.py`. No hardcoded values anywhere else in the codebase.

**Rule: Idempotent preprocessing.**
Running any preprocessing script twice on the same input must produce identical output. Scripts check whether their output already exists and skip reprocessing if so, unless a `--force` flag is passed.

**Rule: Full test coverage for analysis modules.**
Every function in the `analysis/` directory must have a corresponding unit test in `backend/tests/`. Tests use small synthetic data fixtures, not real TCGA data.

---

## Section 1 — Project Initialization

### 1.1 Repository and Directory Structure

Create the exact directory tree below. Every directory must exist before any code is written. Create placeholder `.gitkeep` files in empty data directories so the structure is committed to version control.

```
CancerGeneValidationCopilot/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── expression.py
│   │   ├── survival.py
│   │   ├── mutation.py
│   │   └── summary.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── expression_analysis.py
│   │   ├── survival_analysis.py
│   │   ├── mutation_analysis.py
│   │   └── ai_summary.py
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── preprocess_expression.py
│   │   ├── preprocess_clinical.py
│   │   └── preprocess_mutation.py
│   │
│   ├── data/
│   │   ├── raw/
│   │   │   ├── expression/
│   │   │   ├── clinical/
│   │   │   └── mutation/
│   │   └── processed/
│   │       ├── expression/
│   │       ├── clinical/
│   │       └── mutation/
│   │
│   ├── cache/
│   │
│   ├── reports/
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── cache_manager.py
│   │   ├── id_normalizer.py
│   │   └── logger.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── fixtures/
│       ├── test_expression.py
│       ├── test_survival.py
│       ├── test_mutation.py
│       └── test_validators.py
│
├── docs/
├── reports/
└── README.md
```

### 1.2 Python Environment

The `requirements.txt` must pin exact versions for every dependency to ensure reproducibility. Include:

- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server
- `pandas` — data processing
- `numpy` — numerical operations
- `scipy` — statistical tests
- `lifelines` — survival analysis
- `plotly` — visualizations
- `kaleido` — static image export from Plotly
- `httpx` — async HTTP client for OpenRouter calls
- `python-dotenv` — environment variable loading
- `pytest` — testing
- `pytest-asyncio` — async test support
- `pyarrow` — Parquet file support
- `openpyxl` — Excel compatibility if needed

Do not include any library not in this list without a documented justification in `docs/dependency_decisions.md`.

### 1.3 Configuration Module

`backend/config.py` is the single source of truth for all configuration. It must define:

**Paths:**
- Path to each raw data directory, split by data type (expression, clinical, mutation)
- Path to each processed data directory
- Path to the cache directory
- Path to the reports output directory

**Supported cancers:**
- A dictionary mapping each cancer display name to its TCGA project code: BRCA, LUAD, COAD

**Supported genes:**
- This is not a hardcoded list. Instead, config defines the path to the HGNC gene symbol reference file, which the validator loads at startup.

**Statistical thresholds:**
- Default significance threshold (p-value ≤ 0.05)
- Default expression split strategy ("median")
- Minimum required tumor samples (enforce at least 50)
- Minimum required normal samples (enforce at least 10)

**AI configuration:**
- OpenRouter API base URL
- Model name to use (configurable without code changes)
- Max tokens for summary generation
- Temperature for summary generation (keep low, 0.2–0.3)

**Cache configuration:**
- Cache time-to-live in hours
- Whether cache is enabled (boolean flag)

Load all sensitive values (API keys) from a `.env` file using `python-dotenv`. The config module must raise a `EnvironmentConfigurationError` at startup if required environment variables are missing.

---

## Section 2 — Data Acquisition Guide

> This section tells the agent exactly which files to download and where to place them. The agent does not automate downloading — it documents the exact procedure so a human can acquire the files, after which the agent processes them.

### 2.1 Expression Data

**Source:** UCSC Xena Browser — `https://xenabrowser.net`

**Dataset to use:** `TCGA TARGET GTEx` study, specifically the file:

```
TcgaTargetGtex_rsem_gene_tpm
```

This is a large gene expression matrix where:
- Rows are gene identifiers (Ensembl IDs with version suffixes)
- Columns are sample identifiers (TCGA barcodes and GTEx sample IDs)
- Values are log2(TPM + 0.001) expression values

**Accompanying phenotype/metadata file:** Download the sample phenotype file from the same TCGA TARGET GTEx cohort on Xena. This file maps each sample ID to:
- Sample type (Primary Tumor, Solid Tissue Normal, GTEx normal, etc.)
- Primary disease or tissue of origin (to filter by cancer type)

**Placement:** Place both files in `backend/data/raw/expression/`

**Expected file sizes:** The expression matrix is several gigabytes. Do not attempt to load it entirely into memory during analysis. Preprocessing will extract cancer-specific subsets.

### 2.2 Clinical Survival Data

**Source:** UCSC Xena Browser — same cohort or TCGA Pan-Cancer clinical data

**Required file:** The TCGA clinical phenotype file that includes:
- `_PATIENT` or `sample` column (sample identifier)
- `OS` (overall survival event: 0 = censored, 1 = event/death)
- `OS.time` (overall survival time in days)
- `PFI`, `PFI.time` (progression-free interval, optional but include if available)
- `cancer type abbreviation` column

If the unified Pan-Cancer clinical file is used, it must contain all three cancer types (BRCA, LUAD, COAD) so a single file covers all analysis.

**Placement:** Place in `backend/data/raw/clinical/`

### 2.3 Mutation Data

**Source:** cBioPortal — `https://www.cbioportal.org`

**For each of the three cancers, download the TCGA dataset mutation file:**
- TCGA Breast Invasive Carcinoma (BRCA) — download mutations (MAF format)
- TCGA Lung Adenocarcinoma (LUAD) — download mutations (MAF format)
- TCGA Colon Adenocarcinoma (COAD) — download mutations (MAF format)

From each dataset, select "Download" and choose the mutation data tab. The mutation file is a MAF-style tab-separated file containing columns including:
- `Hugo_Symbol` — gene name
- `Tumor_Sample_Barcode` — patient/sample identifier
- `Variant_Classification` — type of mutation (Missense, Nonsense, etc.)
- `Variant_Type` — SNP, DNP, INS, DEL, etc.

**Placement:** Name files clearly by cancer and place in `backend/data/raw/mutation/`:
- `brca_mutations.txt`
- `luad_mutations.txt`
- `coad_mutations.txt`

### 2.4 HGNC Gene Symbol Reference

**Source:** HGNC (Human Genome Nomenclature Committee) — download the complete approved gene symbol list as a flat file (TSV).

This file is used exclusively by the validator to confirm whether a user-submitted gene symbol is a valid, approved HGNC symbol.

**Placement:** `backend/data/raw/hgnc_approved_symbols.txt`

---

## Section 3 — Preprocessing Pipeline

> Preprocessing scripts run once before the server starts. They convert raw data into clean, cancer-specific, analysis-ready files stored in `backend/data/processed/`. Analysis modules never touch raw data.

### 3.1 Expression Preprocessing

**Script:** `backend/preprocessing/preprocess_expression.py`

**What it must do, in order:**

**Step 1 — Load the phenotype metadata file.**
Read only the columns needed: sample ID, sample type, and primary disease/tissue. Do not load the entire expression matrix yet.

**Step 2 — Filter phenotype to relevant samples.**
From the phenotype file, extract three separate sample lists:
- For BRCA: all samples labeled as BRCA primary tumor, and all samples labeled as solid tissue normal from BRCA patients
- For LUAD: same logic for LUAD
- For COAD: same logic for COAD

Also extract GTEx normal tissue samples for the relevant tissues (breast, lung, colon) to supplement normal groups where TCGA normal sample counts are low. GTEx samples are labeled differently in the phenotype file — handle this by checking the sample type column for GTEx-specific labels.

**Step 3 — Load expression matrix in chunks.**
Because the expression matrix is extremely large, load it using chunked reading. For each chunk, keep only the columns (samples) that appear in the relevant sample lists. Discard all other columns immediately. This dramatically reduces memory pressure.

**Step 4 — Convert Ensembl IDs to HGNC gene symbols.**
The expression matrix uses Ensembl IDs (e.g., ENSG00000141510.11). Strip version suffixes and map to HGNC gene symbols using a mapping table. If multiple Ensembl IDs map to the same gene symbol, keep the one with highest mean expression across samples (most likely the canonical isoform). Discard any rows that cannot be mapped.

**Step 5 — Separate tumor and normal samples.**
For each cancer, produce two DataFrames:
- Tumor expression: rows = genes, columns = tumor sample IDs
- Normal expression: rows = genes, columns = normal sample IDs (TCGA normals + GTEx normals combined)

**Step 6 — Save processed files.**
Save each DataFrame as a Parquet file with gene symbols as the index. Use Parquet because it is faster to load than CSV and preserves data types. Name files clearly:
- `backend/data/processed/expression/brca_tumor.parquet`
- `backend/data/processed/expression/brca_normal.parquet`
- (same pattern for LUAD and COAD)

**Step 7 — Save a gene index file.**
Save the list of all valid gene symbols present in the processed expression data as a plain text file, one symbol per line. The validator uses this to quickly confirm whether a queried gene exists in the dataset before running any analysis.

**Validation after preprocessing:**
Log the number of tumor samples and normal samples for each cancer. If either count falls below the configured minimums, raise a warning (not an error — analysis can still run with reduced power, but the researcher must be told).

---

### 3.2 Clinical Data Preprocessing

**Script:** `backend/preprocessing/preprocess_clinical.py`

**What it must do, in order:**

**Step 1 — Load the raw clinical file.**
Load the TCGA clinical metadata. Identify the columns for: sample ID, cancer type, overall survival time, overall survival event status. Column names vary between Xena clinical files — handle multiple known naming conventions (e.g., `OS`, `OS_STATUS`, `overall_survival`).

**Step 2 — Standardize sample IDs.**
TCGA sample IDs appear in multiple formats (15-character, 16-character, with or without sample type suffix). Normalize all sample IDs to the 12-character patient barcode format (first 12 characters, uppercase, hyphens preserved). Store the normalized ID in a new column and keep the original for traceability.

**Step 3 — Convert survival event status to binary.**
The survival event column may contain values like `1:DECEASED`, `0:LIVING`, `DECEASED`, `1`, `0`, `TRUE`, `FALSE`. Convert all of these to integer 0 (censored/alive) or 1 (event/death). If a value cannot be parsed, set it to NaN and log the original value and sample ID.

**Step 4 — Remove invalid rows.**
Drop any row where:
- Survival time is NaN
- Survival time is zero or negative
- Survival event status is NaN
- Sample ID is missing

Log how many rows were removed and why.

**Step 5 — Separate by cancer type.**
Split the cleaned DataFrame into three separate DataFrames, one per cancer. Save each as a Parquet file:
- `backend/data/processed/clinical/brca_survival.parquet`
- `backend/data/processed/clinical/luad_survival.parquet`
- `backend/data/processed/clinical/coad_survival.parquet`

Each file must contain exactly three columns: normalized sample ID, survival time (days, numeric), survival event (0 or 1).

---

### 3.3 Mutation Data Preprocessing

**Script:** `backend/preprocessing/preprocess_mutation.py`

**What it must do, in order:**

**Step 1 — Load each cancer's raw mutation MAF file.**
These files have comment lines at the top (starting with `#`). Skip comment lines. Load only the necessary columns: `Hugo_Symbol`, `Tumor_Sample_Barcode`, `Variant_Classification`, `Variant_Type`.

**Step 2 — Normalize sample IDs.**
Apply the same 12-character patient barcode normalization used in clinical preprocessing. Mutation files use full TCGA barcodes — truncate to 12 characters.

**Step 3 — Standardize mutation classifications.**
Map verbose Variant_Classification values to simplified categories:
- `Missense_Mutation` → Missense
- `Nonsense_Mutation` → Nonsense
- `Frame_Shift_Del`, `Frame_Shift_Ins` → Frameshift
- `Splice_Site` → Splice Site
- `In_Frame_Del`, `In_Frame_Ins` → In-frame Indel
- `Silent` → Silent
- All others → Other

**Step 4 — Compute cohort sizes.**
For each cancer, count the total number of unique patients in the MAF file. Store this as a metadata value alongside the mutation data. This is required for frequency normalization.

**Step 5 — Save processed files.**
Save each cancer's processed mutation DataFrame as a Parquet file:
- `backend/data/processed/mutation/brca_mutations.parquet`
- `backend/data/processed/mutation/luad_mutations.parquet`
- `backend/data/processed/mutation/coad_mutations.parquet`

Save cohort sizes in a JSON metadata file at:
- `backend/data/processed/mutation/cohort_sizes.json`

---

### 3.4 Preprocessing Orchestrator

Create a single entry-point script `backend/preprocessing/run_all.py` that:
1. Checks whether processed files already exist (idempotent check)
2. Runs expression preprocessing if needed
3. Runs clinical preprocessing if needed
4. Runs mutation preprocessing if needed
5. Accepts a `--force` flag to rerun all preprocessing regardless

The server startup routine (`app.py`) calls this orchestrator on launch and logs the result. If any preprocessing step fails, startup must halt with a clear error message.

---

## Section 4 — Utility Modules

Build all utilities before writing any analysis or route code. Analysis modules depend on these.

### 4.1 Logger

**File:** `backend/utils/logger.py`

Create a centralized logger that:
- Writes structured log entries (timestamp, level, module name, message, optional metadata dict)
- Outputs to both the console and a rotating log file at `backend/logs/app.log`
- Supports DEBUG, INFO, WARNING, ERROR levels
- Is imported and used by every other module rather than using `print()`

All analysis functions must log their inputs (gene, cancer) at INFO level when they begin, and log their outputs (sample counts, p-values) at INFO level when they complete. Errors always log at ERROR level with the full exception details.

### 4.2 Gene and Input Validator

**File:** `backend/utils/validators.py`

This module performs all input validation before any analysis runs. It must implement:

**Gene symbol validator:**
- Load the HGNC approved gene symbol list at module import time (once, cached in memory)
- Also load the gene index file produced during expression preprocessing (genes actually present in the dataset)
- Validate that a submitted gene symbol: is a non-empty string, is uppercase, matches an HGNC approved symbol, and exists in the processed expression data
- Return a structured result: valid (boolean), normalized symbol (uppercase), error message if invalid

**Cancer type validator:**
- Accept only the three supported TCGA codes: BRCA, LUAD, COAD
- Case-insensitive input (normalize to uppercase)
- Return structured result: valid (boolean), normalized code, error message if invalid

**Analysis request validator:**
- Combine both validators into a single call that validates a complete analysis request
- Returns all errors at once rather than failing on the first one

### 4.3 Sample ID Normalizer

**File:** `backend/utils/id_normalizer.py`

This module provides the single canonical function for normalizing TCGA sample IDs to 12-character patient barcodes. It is imported by both preprocessing scripts and analysis modules to ensure consistency. It must handle all known TCGA barcode formats without error.

### 4.4 Cache Manager

**File:** `backend/utils/cache_manager.py`

Implement a file-based cache with the following behavior:

- Cache keys are deterministic strings derived from the analysis type, gene symbol, and cancer type
- Cache entries are stored as JSON files in `backend/cache/`
- Each cache file includes the result data and a timestamp
- The cache manager checks whether an entry exists and is within the configured time-to-live before returning it
- Cache writes are atomic (write to a temp file, then rename) to avoid partial writes
- A cache invalidation function clears all entries or entries matching a specific key pattern
- The cache manager respects the `cache_enabled` flag from config — if disabled, it always returns cache miss

The cache stores the complete JSON-serializable result of each analysis (statistics + plot data), not just statistics. This means a cache hit returns a fully populated response without re-running any computation.

---

## Section 5 — Analysis Modules

> These are the scientific core of the platform. Build them in order. Each module has strict input/output contracts. Do not deviate from these contracts.

### 5.1 Expression Analysis Module

**File:** `backend/analysis/expression_analysis.py`

**Purpose:** Compute differential expression of a single gene between tumor and normal tissue for a given cancer type.

**Inputs (as function arguments, not HTTP):**
- Gene symbol (validated, uppercase string)
- Cancer type (validated TCGA code)

**Processing steps, in order:**

**Step 1 — Load processed expression data.**
Load the tumor and normal Parquet files for the specified cancer. Load only the row corresponding to the requested gene (do not load the entire matrix into memory — use Pandas index-based row selection on a Parquet file).

**Step 2 — Extract expression vectors.**
Produce two 1D arrays: tumor expression values and normal expression values for the gene. Both are arrays of log2(TPM + 0.001) values.

**Step 3 — Compute descriptive statistics.**
For both groups compute: mean, median, standard deviation, min, max, and sample count.

**Step 4 — Compute fold change.**
Fold change is computed in TPM space, not log space:
- Convert log2 values back to TPM: `TPM = 2^(log2_value) - 0.001`
- Compute mean tumor TPM and mean normal TPM
- Fold change = mean tumor TPM / mean normal TPM (guard against division by zero)
- Log2 fold change = log2(fold change)

**Step 5 — Select and run the appropriate statistical test.**
Test normality of both groups using the Shapiro–Wilk test (use a random subsample of up to 5000 values if groups are large, because Shapiro–Wilk does not scale to very large N). If both groups pass normality, run Welch's t-test. If either group fails normality, run Mann–Whitney U test. Record which test was used.

**Step 6 — Generate the visualization.**
Create a combination boxplot + violin plot using Plotly:
- X-axis: two groups labeled "Tumor (N=X)" and "Normal (N=Y)" where X and Y are actual sample counts
- Y-axis: log2(TPM + 0.001) expression
- Show individual data points as a jitter overlay on top of the violin (use a random sample of up to 200 points per group for legibility if groups are large)
- Annotate the plot with the p-value and the test name
- Color scheme: use a muted, scientific color palette (not neon colors)
- Include a plot title: "{GENE} Expression in {CANCER} Tumor vs Normal"
- Serialize the plot as a Plotly JSON object (not a PNG at this stage — the frontend renders it interactively)

**Output contract (Python dict, fully populated, no None values allowed):**
```
{
  "gene": string,
  "cancer": string,
  "tumor_count": integer,
  "normal_count": integer,
  "tumor_mean_log2": float,
  "normal_mean_log2": float,
  "fold_change": float,
  "log2_fold_change": float,
  "p_value": float,
  "statistical_test": string,
  "significant": boolean,
  "direction": string (one of "upregulated", "downregulated", "unchanged"),
  "plot_json": dict (Plotly figure as JSON)
}
```

The `direction` field is "upregulated" if log2FC > 1 and p < threshold, "downregulated" if log2FC < -1 and p < threshold, otherwise "unchanged".

---

### 5.2 Survival Analysis Module

**File:** `backend/analysis/survival_analysis.py`

**Purpose:** Determine whether high vs. low expression of a gene is associated with patient overall survival.

**Inputs:**
- Gene symbol (validated)
- Cancer type (validated)
- Split strategy (string: "median" for MVP; module must be architecturally ready to accept "quartile" or "percentile" later without refactoring)

**Processing steps, in order:**

**Step 1 — Load expression data for tumor samples only.**
Extract the gene's expression vector from the tumor Parquet file for the specified cancer.

**Step 2 — Load clinical survival data.**
Load the processed survival Parquet file for the specified cancer. This gives sample ID, survival time, and event status.

**Step 3 — Merge expression and survival data.**
Normalize both sets of sample IDs using the id_normalizer. Perform an inner join on patient ID. Log how many samples were lost in the merge and why (ID format mismatch is the most common cause).

**Step 4 — Split patients into high and low expression groups.**
For "median" strategy: split at the median expression value. Patients above the median are "High", at or below are "Low". Do not include the exact median boundary in both groups.

**Step 5 — Validate group sizes.**
After splitting, confirm both groups have at least 20 patients. If either group is smaller, return an error result rather than running an underpowered analysis.

**Step 6 — Run Kaplan–Meier estimation.**
Using `lifelines.KaplanMeierFitter`:
- Fit separately for the High and Low expression groups
- Extract median survival time for both groups
- Compute 95% confidence intervals

**Step 7 — Run log-rank test.**
Using `lifelines.statistics.logrank_test`:
- Compare High vs Low groups
- Extract test statistic and p-value

**Step 8 — Compute hazard ratio.**
Using `lifelines.CoxPHFitter`:
- Create a binary covariate (1 = High, 0 = Low)
- Fit a univariate Cox proportional hazards model
- Extract hazard ratio and 95% confidence interval from the model summary

**Step 9 — Generate the Kaplan–Meier plot.**
Using Plotly:
- Two survival curves: High Expression (one color) and Low Expression (another color)
- X-axis: time in days (label as "Overall Survival Time (Days)")
- Y-axis: survival probability (0 to 1, labeled as "Survival Probability")
- Include confidence interval bands as shaded areas
- Annotate with: p-value, hazard ratio with 95% CI, sample counts for each group
- Include a legend identifying the two curves
- Title: "{GENE} Survival Analysis in {CANCER}"

**Output contract:**
```
{
  "gene": string,
  "cancer": string,
  "high_count": integer,
  "low_count": integer,
  "median_survival_high": float (days),
  "median_survival_low": float (days),
  "logrank_p_value": float,
  "hazard_ratio": float,
  "hr_confidence_interval": [float, float],
  "significant": boolean,
  "split_strategy": string,
  "split_value": float (the actual cutoff used),
  "plot_json": dict
}
```

---

### 5.3 Mutation Analysis Module

**File:** `backend/analysis/mutation_analysis.py`

**Purpose:** Report mutation frequency and type distribution for the queried gene in the specified cancer.

**Inputs:**
- Gene symbol (validated)
- Cancer type (validated)

**Processing steps, in order:**

**Step 1 — Load processed mutation data.**
Load the mutation Parquet file for the specified cancer. Load the cohort size from the JSON metadata file.

**Step 2 — Filter for the queried gene.**
Filter the mutation DataFrame to rows where `Hugo_Symbol` matches the gene. If no mutations exist for this gene, this is a valid result (not an error) — return a result indicating zero mutations with a note.

**Step 3 — Compute patient-level mutation frequency.**
Count the number of unique mutated patients (unique sample IDs in the filtered DataFrame). Divide by cohort size to get the mutation rate as a percentage. This is the primary frequency metric.

**Step 4 — Compute mutation type distribution.**
Group by the standardized mutation category and count occurrences. Compute the percentage of each type relative to total mutations in the gene (not relative to cohort — this is a different normalization).

**Step 5 — Generate visualizations.**
Create two Plotly figures:

Figure 1 — Mutation frequency card visualization:
- A single-bar horizontal bar chart showing mutation rate percentage
- Annotated with: "{X}% of {N} patients" where X is the rate and N is cohort size
- Include a reference bar showing the baseline mutation rate across all genes for context (compute this during preprocessing and store it in the metadata JSON)
- Title: "{GENE} Mutation Frequency in {CANCER}"

Figure 2 — Mutation type distribution:
- A pie chart or donut chart showing the percentage breakdown of mutation types
- Label each segment with type name and percentage
- If a gene has zero mutations, return a placeholder figure with a "No mutations detected" annotation rather than an empty chart
- Title: "{GENE} Mutation Types in {CANCER}"

**Output contract:**
```
{
  "gene": string,
  "cancer": string,
  "cohort_size": integer,
  "mutated_patients": integer,
  "mutation_frequency_percent": float,
  "mutation_types": {
    "Missense": integer,
    "Nonsense": integer,
    "Frameshift": integer,
    "Splice Site": integer,
    "In-frame Indel": integer,
    "Silent": integer,
    "Other": integer
  },
  "has_mutations": boolean,
  "frequency_plot_json": dict,
  "type_plot_json": dict
}
```

---

### 5.4 AI Interpretation Module

**File:** `backend/analysis/ai_summary.py`

**Purpose:** Generate a concise, scientifically grounded interpretation of the combined analysis results using the OpenRouter API.

**Inputs:**
- Complete expression result dict
- Complete survival result dict
- Complete mutation result dict

**Critical constraint:** The AI module must never be called without all three analysis results fully populated. Validate this at the function entry point.

**Prompt construction rules:**

The prompt sent to the LLM must be entirely composed of structured numerical data extracted from the three result dicts. It must include:
- Gene name and cancer type
- Expression: fold change, log2FC, p-value, direction, sample counts, test used
- Survival: hazard ratio with CI, p-value, median survival for high and low groups, significance
- Mutation: mutation frequency percent, cohort size, most common mutation type

The prompt must explicitly instruct the model to:
- Write 3–5 sentences maximum
- Use only the provided statistics — do not reference external knowledge or databases
- State whether the gene shows evidence of being a potential prognostic biomarker based solely on the provided data
- Use hedged scientific language ("suggests", "is associated with", "may indicate") rather than definitive causal claims
- Never mention specific drugs, therapies, or treatment recommendations

**API call implementation:**
- Use `httpx` with async HTTP to call the OpenRouter `/v1/chat/completions` endpoint
- Include the model name from config
- Set temperature to the configured value (low, to reduce hallucination risk)
- Implement a timeout (30 seconds maximum)
- Implement one retry on timeout or server error
- If the API call fails after retry, return a fallback summary constructed entirely from the statistical data without LLM generation (a templated string filled with the actual numbers)

**Output contract:**
```
{
  "summary": string,
  "generated_by": string ("ai" or "fallback_template"),
  "model_used": string (or "template" if fallback)
}
```

---

## Section 6 — FastAPI Routes

### 6.1 Application Entry Point

**File:** `backend/app.py`

This file creates and configures the FastAPI application. It must:
- Run the preprocessing orchestrator on startup and halt if it fails
- Register all routers with appropriate prefixes
- Configure CORS to allow the React frontend to call the API (allow localhost:3000 in development)
- Mount a static files directory at `/reports` so generated PDF reports can be downloaded by URL
- Configure global exception handlers that return structured JSON error responses for all unhandled exceptions
- Log the application startup time and the version

### 6.2 Request and Response Models

Create Pydantic models for all request bodies and response payloads. Place these in `backend/models.py`.

**AnalysisRequest model:**
- `gene`: string (will be validated by the validator)
- `cancer`: string (will be validated by the validator)

**Full analysis response model:**
Structured to contain all four analysis result sections as nested objects, plus a top-level status field and a report download URL if the report was successfully generated.

### 6.3 POST /analyze (Master Endpoint)

**File:** `backend/routes/summary.py`

This is the primary endpoint a frontend client calls. It orchestrates all four modules and returns a single unified response.

**Implementation order inside the handler:**
1. Validate the request using the validator module — return 422 with structured error if invalid
2. Check the cache for a hit — return cached result immediately if found
3. Run expression analysis
4. Run survival analysis
5. Run mutation analysis
6. Run AI interpretation (passing all three results)
7. Assemble the unified response
8. Write to cache
9. Trigger PDF report generation asynchronously (do not make the client wait for this)
10. Return the unified response

Steps 3, 4, and 5 must run concurrently using `asyncio.gather` where possible. Each analysis function must be implemented as async-compatible (wrap CPU-bound Pandas/SciPy work in `asyncio.run_in_executor` to avoid blocking the event loop).

If any of the three analysis steps fails, the endpoint must still return a response. The failing section's data is replaced with an error object describing what failed and why. The AI interpretation only runs if at least two of three analysis modules succeeded.

### 6.4 POST /expression

**File:** `backend/routes/expression.py`

Individual endpoint for expression analysis only. Useful for the frontend to re-run individual modules. Calls expression_analysis module directly, applies caching, returns the expression output contract as JSON.

### 6.5 POST /survival

**File:** `backend/routes/survival.py`

Individual endpoint for survival analysis only. Same pattern as expression.

### 6.6 POST /mutation

**File:** `backend/routes/mutation.py`

Individual endpoint for mutation analysis only. Same pattern as expression.

### 6.7 GET /validate

Query parameters: `gene`, `cancer`

Returns validation result before the frontend submits a full analysis. The frontend uses this to show real-time input validation feedback as the user types. This endpoint is not cached (it is fast enough to run on every call).

### 6.8 GET /genes

Returns the full list of gene symbols available in the processed expression data. The frontend uses this for autocomplete. This list is loaded once at startup and kept in memory.

### 6.9 GET /health

Returns server status, preprocessing completion status, and a timestamp. Used by deployment infrastructure.

---

## Section 7 — Report Generation

**File:** `backend/utils/report_generator.py`

This module generates a downloadable PDF report from a complete analysis result.

**Implementation approach:** Use Plotly's static image export (via `kaleido`) to render each plot as a high-resolution PNG. Then assemble the PNG images alongside text blocks into a PDF using the `reportlab` library (add `reportlab` to requirements.txt).

**Report structure:**
1. Cover page: gene name, cancer type, analysis date, dataset sources cited
2. Expression analysis section: the boxplot/violin PNG, followed by a text table showing all numeric outputs (fold change, p-value, sample counts, test used)
3. Survival analysis section: the KM curve PNG, followed by a text table (HR, CI, p-value, median survivals)
4. Mutation analysis section: both mutation plots as PNGs, followed by a text table (frequency, cohort size, type breakdown)
5. AI interpretation section: the generated summary text in a styled block
6. Data sources section: a formatted list of dataset citations

**Report file naming:** `{GENE}_{CANCER}_{timestamp}.pdf`, stored in `backend/reports/`. The report URL returned in the API response points to the mounted static files route at `/reports/{filename}`.

Report generation runs asynchronously after the main API response is sent. If it fails, log the error but do not surface it to the client — the analysis response is already delivered.

---

## Section 8 — Error Handling Specification

Every error returned by any endpoint must follow this JSON structure:
```
{
  "error": true,
  "error_code": string,
  "message": string,
  "details": object or null
}
```

Define the following error codes and ensure they are used consistently:

| Error Code | Meaning |
|---|---|
| `INVALID_GENE` | Gene symbol not found in HGNC or not in dataset |
| `INVALID_CANCER` | Cancer type not in supported list |
| `INSUFFICIENT_SAMPLES` | Too few samples for reliable analysis |
| `MERGE_FAILURE` | Expression and clinical data could not be joined |
| `STATISTICAL_FAILURE` | Statistical test raised an exception |
| `AI_UNAVAILABLE` | OpenRouter API call failed and fallback was used |
| `PREPROCESSING_INCOMPLETE` | Required processed data file is missing |
| `CACHE_ERROR` | Cache read/write failed (non-fatal, log and continue) |

Never return a raw Python exception traceback in an API response. Log the traceback internally, return only the structured error to the client.

---

## Section 9 — Testing Requirements

### 9.1 Test Fixtures

Create small synthetic datasets in `backend/tests/fixtures/` that mimic the structure of processed files:
- A small expression Parquet (50 genes × 30 tumor samples + 15 normal samples)
- A small clinical Parquet (30 patients with survival data)
- A small mutation Parquet (a few hundred rows)

These fixtures must be deterministically generated (seeded random numbers) so tests are reproducible.

### 9.2 Required Tests

**Expression analysis tests:**
- Test that fold change is correctly computed for a known synthetic case
- Test that the correct statistical test is chosen based on distribution
- Test that the output contract is fully populated (no missing keys, no None values)
- Test behavior when the gene is not found in the expression data

**Survival analysis tests:**
- Test that the median split produces two groups of approximately equal size
- Test that KM fitting and log-rank test run without error on synthetic data
- Test that hazard ratio is extracted correctly
- Test behavior when one group has fewer than 20 patients

**Mutation analysis tests:**
- Test frequency normalization by cohort size
- Test that a gene with zero mutations returns a valid result (not an error)
- Test mutation type categorization mapping

**Validator tests:**
- Test that invalid gene symbols are rejected
- Test that valid symbols pass
- Test that cancer type validation is case-insensitive
- Test that combined validator returns all errors simultaneously

### 9.3 Test Execution

All tests must pass before the implementation is considered complete. Run tests with:
```
pytest backend/tests/ -v --tb=short
```

---

## Section 10 — Performance and Scalability Rules

**Never load the full expression matrix during analysis.** Preprocessing extracts cancer-specific subsets. Analysis loads only the specific gene row from Parquet files. Parquet column-oriented storage makes single-row access extremely fast.

**Use connection pooling for the OpenRouter HTTP client.** Instantiate the `httpx.AsyncClient` once at application startup and reuse it across requests. Do not create a new client per request.

**Set Pandas copy-on-write behavior.** After Pandas 2.0, enable copy-on-write globally to avoid silent data mutation bugs in filtering pipelines.

**Monitor memory usage during preprocessing.** The raw expression matrix is multi-gigabyte. Chunked loading is mandatory. After each chunk is processed and subsetted, explicitly delete the chunk object and call garbage collection to prevent memory accumulation.

**Do not block the FastAPI event loop.** All Pandas, NumPy, SciPy, and Lifelines operations are CPU-bound and blocking. Wrap them in `loop.run_in_executor(None, sync_function)` to run them in a thread pool without blocking async request handling.

---

## Section 11 — Implementation Sequence (Agent Execution Order)

Execute these phases strictly in order. Do not start a phase until all checklist items in the previous phase are complete.

### Phase 1 — Foundation
- [ ] Create complete directory structure
- [ ] Write `requirements.txt` with pinned versions
- [ ] Write `backend/config.py` fully
- [ ] Write `backend/utils/logger.py`
- [ ] Write `backend/utils/id_normalizer.py`
- [ ] Write `backend/utils/validators.py`
- [ ] Write `backend/utils/cache_manager.py`

### Phase 2 — Preprocessing
- [ ] Write `backend/preprocessing/preprocess_expression.py`
- [ ] Write `backend/preprocessing/preprocess_clinical.py`
- [ ] Write `backend/preprocessing/preprocess_mutation.py`
- [ ] Write `backend/preprocessing/run_all.py`
- [ ] Verify all scripts are idempotent
- [ ] Verify all scripts produce the correct output file names and formats

### Phase 3 — Analysis Modules
- [ ] Write `backend/analysis/expression_analysis.py` fully
- [ ] Write `backend/analysis/survival_analysis.py` fully
- [ ] Write `backend/analysis/mutation_analysis.py` fully
- [ ] Write `backend/analysis/ai_summary.py` fully including fallback template
- [ ] Verify all output contracts are fully populated with no None values

### Phase 4 — Tests
- [ ] Create all synthetic test fixtures
- [ ] Write all test files
- [ ] Run tests — all must pass before continuing

### Phase 5 — API Layer
- [ ] Write `backend/models.py` with all Pydantic models
- [ ] Write all route files
- [ ] Write `backend/app.py` with startup routine, CORS, and exception handlers
- [ ] Write `backend/utils/report_generator.py`

### Phase 6 — Integration Verification
- [ ] Start the server with `uvicorn backend.app:app --reload`
- [ ] Confirm `/health` returns 200
- [ ] Confirm `/genes` returns a populated list
- [ ] Confirm `/validate?gene=TP53&cancer=BRCA` returns valid: true
- [ ] Confirm `POST /analyze` with `{"gene": "TP53", "cancer": "BRCA"}` returns all four sections populated
- [ ] Confirm a PDF report is generated in `backend/reports/`
- [ ] Confirm `POST /analyze` with an invalid gene returns the correct structured error
- [ ] Confirm a second identical request returns from cache (verify by checking logs)

### Phase 7 — Final Checks
- [ ] Run the full test suite — all pass
- [ ] Verify no hardcoded values outside `config.py`
- [ ] Verify all log messages are informative and correctly leveled
- [ ] Verify all output contracts match their specifications exactly
- [ ] Write `README.md` with setup instructions, data acquisition guide, and API documentation

---

## Section 12 — README Requirements

The `README.md` must document:

1. Project overview (2–3 sentences)
2. Data acquisition: exact steps to download each dataset with source URLs and expected filenames
3. Environment setup: how to create the Python environment and install dependencies
4. Configuration: which environment variables are required and what they do
5. Running preprocessing: the command to run and what output to expect
6. Running the server: the command and the URL to access the API docs
7. API reference: each endpoint, its request format, and its response format
8. Running tests: the command and expected output
9. Limitations and known constraints: minimum sample size requirements, supported cancers, supported genes

---

*End of Blueprint. The agent now has everything needed to implement a fully finished, production-ready Cancer Gene Validation Copilot backend. Begin with Phase 1.*
