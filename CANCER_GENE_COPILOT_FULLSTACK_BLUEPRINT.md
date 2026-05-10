# Cancer Gene Validation Copilot — Full-Stack AI Agent Implementation Blueprint

> **Instructions for the AI Agent:**
> This document is your complete implementation guide for the entire full-stack application — backend and frontend. You will read it top to bottom, execute every phase in the order defined in Section 13, and never skip a phase. Each phase has a checklist. You do not move to the next phase until every item in the current phase checklist is fully implemented, tested, and working. If you encounter an ambiguity, resolve it using the rules in Section 0 before continuing. The goal is a fully finished, production-ready application — not a prototype, not a demo, not a skeleton.

---

## Section 0 — Global Rules (Read First, Apply Always)

These rules govern every decision you make throughout this entire project — backend and frontend alike. They override any shortcut or simplification you might consider.

**Rule: No placeholders, ever.**
Every function, component, route, module, and utility must be fully implemented. Do not write `# TODO`, `pass`, stub functions, or `// placeholder` comments. If a module depends on a file that does not yet exist, create that file before writing the module.

**Rule: Fail loudly and informatively.**
Every module must raise specific, descriptive exceptions — never silent failures. Log the exact reason for failure, the input that caused it, and the module it came from. A researcher should be able to read the log and understand exactly what went wrong without reading source code. On the frontend, every error state must be visibly communicated to the user with a meaningful message, never a blank screen or a spinner that never resolves.

**Rule: Strict separation of concerns.**
Backend: data loading, preprocessing, statistical analysis, visualization, and AI interpretation are always separate layers. No analysis function should load raw files. No route handler should perform statistics.
Frontend: API communication, state management, and rendering are always separate concerns. No component should call the API directly — all API calls go through the service layer. No service function should contain rendering logic.

**Rule: All datasets are local.**
You will never call external APIs at analysis time, scrape live websites, or fetch data at runtime. All TCGA, GTEx, and cBioPortal data is predownloaded and stored in the local `backend/data/` directory tree. Preprocessing scripts convert raw data into clean, analysis-ready files. Analysis modules only ever read from processed files.

**Rule: Scientific validity is non-negotiable.**
Every statistical output must include sample counts, p-values, and the name of the statistical test used. Every visualization must show axis labels, sample counts, and significance markers. No result is displayed to the user without these components. The frontend must never render a chart that is missing its annotation data.

**Rule: All configuration lives in one place per layer.**
Backend: all file paths, model names, thresholds, API keys, and environment-specific values live in `backend/config.py`.
Frontend: all API base URLs, environment flags, and application-level constants live in `frontend/src/config.js`. No hardcoded values anywhere else in either codebase.

**Rule: Idempotent preprocessing.**
Running any preprocessing script twice on the same input must produce identical output. Scripts check whether their output already exists and skip reprocessing if so, unless a `--force` flag is passed.

**Rule: Full test coverage for analysis modules and frontend services.**
Every function in `backend/analysis/` must have a corresponding unit test. Every function in `frontend/src/services/` must have a corresponding unit test.

**Rule: The frontend never invents data.**
If the backend returns an error for a module (expression, survival, or mutation), the frontend renders that module's section in an explicit error state. It never shows stale data, zero-filled placeholders, or fabricated values. An honest error message is always better than a misleading result.

---

## Section 1 — Project Initialization

### 1.1 Complete Repository and Directory Structure

Create the exact directory tree below. Every directory must exist before any code is written. Create placeholder `.gitkeep` files in empty data directories.

```
CancerGeneValidationCopilot/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── models.py
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
│   │   ├── preprocess_mutation.py
│   │   └── run_all.py
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
│   ├── reports/
│   ├── logs/
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── cache_manager.py
│   │   ├── id_normalizer.py
│   │   ├── report_generator.py
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
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── index.js
│   │   ├── App.js
│   │   ├── config.js
│   │   │
│   │   ├── pages/
│   │   │   ├── DashboardPage.js
│   │   │   └── AboutPage.js
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.js
│   │   │   │   ├── Sidebar.js
│   │   │   │   └── TopBar.js
│   │   │   │
│   │   │   ├── search/
│   │   │   │   ├── GeneSearchBar.js
│   │   │   │   └── CancerSelector.js
│   │   │   │
│   │   │   ├── metrics/
│   │   │   │   └── SummaryMetricsBar.js
│   │   │   │
│   │   │   ├── expression/
│   │   │   │   ├── ExpressionPanel.js
│   │   │   │   └── ExpressionPlot.js
│   │   │   │
│   │   │   ├── survival/
│   │   │   │   ├── SurvivalPanel.js
│   │   │   │   └── SurvivalPlot.js
│   │   │   │
│   │   │   ├── mutation/
│   │   │   │   ├── MutationPanel.js
│   │   │   │   ├── MutationFrequencyPlot.js
│   │   │   │   └── MutationTypePlot.js
│   │   │   │
│   │   │   ├── interpretation/
│   │   │   │   └── AIInterpretationPanel.js
│   │   │   │
│   │   │   └── shared/
│   │   │       ├── StatCard.js
│   │   │       ├── SectionPanel.js
│   │   │       ├── LoadingOverlay.js
│   │   │       ├── ErrorBlock.js
│   │   │       ├── Badge.js
│   │   │       └── DownloadButton.js
│   │   │
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── analysisService.js
│   │   │   └── geneService.js
│   │   │
│   │   ├── state/
│   │   │   ├── analysisContext.js
│   │   │   └── analysisReducer.js
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAnalysis.js
│   │   │   └── useGeneAutocomplete.js
│   │   │
│   │   ├── styles/
│   │   │   ├── global.css
│   │   │   ├── variables.css
│   │   │   ├── typography.css
│   │   │   └── components.css
│   │   │
│   │   └── tests/
│   │       ├── services/
│   │       │   ├── analysisService.test.js
│   │       │   └── geneService.test.js
│   │       └── components/
│   │           ├── GeneSearchBar.test.js
│   │           └── SummaryMetricsBar.test.js
│   │
│   ├── package.json
│   └── .env
│
├── docs/
│   └── dependency_decisions.md
├── reports/
└── README.md
```

### 1.2 Python Backend Environment

The `requirements.txt` must pin exact versions for every dependency. Include:

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
- `reportlab` — PDF generation
- `openpyxl` — Excel compatibility if needed

### 1.3 JavaScript Frontend Environment

`frontend/package.json` must declare exact versions for every dependency. Include:

- `react` and `react-dom` — UI framework
- `react-router-dom` — client-side routing between Dashboard and About pages
- `plotly.js-dist-min` — lightweight Plotly bundle for rendering backend-generated Plotly JSON
- `react-plotly.js` — React wrapper for Plotly
- `axios` — HTTP client for API calls
- `@testing-library/react` and `@testing-library/jest-dom` — component testing
- `jest` — test runner

Do not add any UI component library (no Material UI, no Ant Design, no Chakra). The entire visual design is built with plain CSS3 as specified. Do not add any state management library (no Redux, no Zustand). Use React Context and useReducer as specified in Section 11.

### 1.4 Backend Configuration Module

`backend/config.py` is the single source of truth for all backend configuration. It must define:

**Paths:** Raw and processed data directories for expression, clinical, and mutation data. Cache directory. Reports directory. Log directory.

**Supported cancers:** A dictionary mapping display names to TCGA codes for BRCA, LUAD, and COAD.

**Statistical thresholds:** Significance threshold (p ≤ 0.05), default split strategy ("median"), minimum tumor samples (50), minimum normal samples (10).

**AI configuration:** OpenRouter API base URL, model name, max tokens (1000), temperature (0.2).

**Cache configuration:** Time-to-live in hours, enabled boolean flag.

Load all sensitive values from a `.env` file. Raise `EnvironmentConfigurationError` at startup if required environment variables are missing.

### 1.5 Frontend Configuration Module

`frontend/src/config.js` is the single source of truth for all frontend configuration. It must define:

- The backend API base URL, loaded from the `.env` file at build time (e.g., `REACT_APP_API_BASE_URL`)
- The list of supported cancer types with their display labels and TCGA codes
- The polling interval for async report generation status (if implemented)
- Any feature flags (e.g., `REACT_APP_SHOW_ABOUT_PAGE`)

No component or service should hardcode `localhost:8000` or any URL. All API communication goes through `config.js`.

---

## Section 2 — Data Acquisition Guide

> This section tells the agent exactly which files to download and where to place them. The agent does not automate downloading — it documents the exact procedure so a human can acquire the files, after which the agent processes them.

### 2.1 Expression Data

**Source:** UCSC Xena Browser — `https://xenabrowser.net`

**Dataset:** `TCGA TARGET GTEx` study, file:
```
TcgaTargetGtex_rsem_gene_tpm
```

This is a large gene expression matrix where rows are Ensembl IDs (with version suffixes), columns are sample identifiers (TCGA barcodes and GTEx sample IDs), and values are log2(TPM + 0.001).

Also download the accompanying sample phenotype file from the same cohort. This file maps each sample ID to sample type and primary disease/tissue of origin.

**Placement:** Both files in `backend/data/raw/expression/`

### 2.2 Clinical Survival Data

**Source:** UCSC Xena Browser — TCGA Pan-Cancer clinical data

**Required columns:** Sample ID, cancer type abbreviation, overall survival time (OS.time in days), overall survival event status (OS), and progression-free interval (PFI, PFI.time) if available.

**Placement:** `backend/data/raw/clinical/`

### 2.3 Mutation Data

**Source:** cBioPortal — `https://www.cbioportal.org`

Download the TCGA mutation MAF file for each of the three cancers separately:
- TCGA Breast Invasive Carcinoma (BRCA) mutations → `brca_mutations.txt`
- TCGA Lung Adenocarcinoma (LUAD) mutations → `luad_mutations.txt`
- TCGA Colon Adenocarcinoma (COAD) mutations → `coad_mutations.txt`

Required MAF columns: `Hugo_Symbol`, `Tumor_Sample_Barcode`, `Variant_Classification`, `Variant_Type`.

**Placement:** `backend/data/raw/mutation/`

### 2.4 HGNC Gene Symbol Reference

**Source:** HGNC — download the complete approved gene symbol list as a TSV flat file.

**Placement:** `backend/data/raw/hgnc_approved_symbols.txt`

---

## Section 3 — Preprocessing Pipeline

> Preprocessing scripts run once before the server starts. They convert raw data into clean, cancer-specific, analysis-ready Parquet files. Analysis modules never touch raw data.

### 3.1 Expression Preprocessing

**Script:** `backend/preprocessing/preprocess_expression.py`

**Steps in order:**

**Step 1 — Load phenotype metadata.** Read only sample ID, sample type, and primary disease/tissue columns. Do not load the expression matrix yet.

**Step 2 — Filter phenotype to relevant samples.** For each of the three cancers, build separate lists of tumor samples and normal samples (TCGA matched normals plus GTEx normal tissue samples for the relevant tissue). GTEx samples are identified by their sample type label in the phenotype file. Supplementing with GTEx normals is mandatory because some cancers (especially COAD) have very few TCGA-matched normals.

**Step 3 — Load expression matrix in chunks.** The matrix is multi-gigabyte. Use chunked reading. For each chunk, keep only columns (samples) in the relevant sample lists and discard everything else immediately. After processing each chunk, delete the chunk object and invoke garbage collection.

**Step 4 — Convert Ensembl IDs to HGNC gene symbols.** Strip Ensembl version suffixes. Map to gene symbols using a mapping table. For multiple Ensembl IDs mapping to the same gene symbol, keep the one with highest mean expression (most likely canonical isoform). Discard unmappable rows.

**Step 5 — Separate tumor and normal samples.** Produce two DataFrames per cancer: tumor expression and normal expression (rows = gene symbols, columns = sample IDs).

**Step 6 — Save as Parquet.** Save with gene symbols as the index:
- `backend/data/processed/expression/brca_tumor.parquet`
- `backend/data/processed/expression/brca_normal.parquet`
- Same pattern for LUAD and COAD.

**Step 7 — Save gene index file.** Save the list of all gene symbols present in the processed data as a plain text file at `backend/data/processed/expression/gene_index.txt`, one symbol per line. The validator uses this at startup.

**Validation:** Log tumor and normal sample counts for each cancer. Warn (not error) if either falls below the configured minimums.

### 3.2 Clinical Data Preprocessing

**Script:** `backend/preprocessing/preprocess_clinical.py`

**Steps in order:**

**Step 1 — Load raw clinical file.** Handle multiple known column naming conventions for survival time and event status (e.g., `OS`, `OS_STATUS`, `overall_survival`).

**Step 2 — Standardize sample IDs.** Normalize all sample IDs to 12-character TCGA patient barcodes (uppercase, hyphens preserved) using the id_normalizer utility. Keep original IDs for traceability.

**Step 3 — Convert survival event status to binary.** Map all known formats (`1:DECEASED`, `0:LIVING`, `DECEASED`, `1`, `0`, `TRUE`, `FALSE`) to integer 0 or 1. Log any values that cannot be parsed, then set them to NaN.

**Step 4 — Remove invalid rows.** Drop rows where survival time is NaN, zero, or negative; where event status is NaN; or where sample ID is missing. Log count and reason for each removal.

**Step 5 — Separate by cancer and save:**
- `backend/data/processed/clinical/brca_survival.parquet`
- `backend/data/processed/clinical/luad_survival.parquet`
- `backend/data/processed/clinical/coad_survival.parquet`

Each file contains exactly three columns: normalized sample ID, survival time in days (numeric), event status (0 or 1).

### 3.3 Mutation Data Preprocessing

**Script:** `backend/preprocessing/preprocess_mutation.py`

**Steps in order:**

**Step 1 — Load raw MAF files.** Skip comment lines (starting with `#`). Load only: `Hugo_Symbol`, `Tumor_Sample_Barcode`, `Variant_Classification`, `Variant_Type`.

**Step 2 — Normalize sample IDs.** Truncate to 12-character patient barcodes.

**Step 3 — Standardize mutation classifications.** Map to simplified categories: Missense, Nonsense, Frameshift, Splice Site, In-frame Indel, Silent, Other.

**Step 4 — Compute and store cohort sizes.** Count unique patients per cancer. Store in `backend/data/processed/mutation/cohort_sizes.json`. This is required for frequency normalization.

**Step 5 — Compute and store baseline mutation rates.** For each cancer, compute the median mutation frequency across all genes (mutated patients / cohort size). Store in the same JSON metadata file. The frontend uses this as a reference baseline on the mutation frequency chart.

**Step 6 — Save processed files:**
- `backend/data/processed/mutation/brca_mutations.parquet`
- `backend/data/processed/mutation/luad_mutations.parquet`
- `backend/data/processed/mutation/coad_mutations.parquet`

### 3.4 Preprocessing Orchestrator

**Script:** `backend/preprocessing/run_all.py`

Single entry point that checks for existing processed files (idempotent), runs each preprocessing script in order if outputs are missing, accepts a `--force` flag to rerun everything, and logs completion status for each step.

The server startup routine in `app.py` calls this orchestrator. If any step fails, server startup halts with a clear error.

---

## Section 4 — Backend Utility Modules

Build all utilities before writing any analysis or route code. Analysis modules depend on these.

### 4.1 Logger

**File:** `backend/utils/logger.py`

Centralized structured logger that writes to both console and a rotating log file at `backend/logs/app.log`. Supports DEBUG, INFO, WARNING, ERROR. Every module imports and uses this logger rather than `print()`. All analysis functions log inputs at INFO on start and outputs (sample counts, p-values) at INFO on completion. Errors log at ERROR with full exception details.

### 4.2 Gene and Input Validator

**File:** `backend/utils/validators.py`

**Gene symbol validator:** Loads the HGNC approved symbol list and the gene index file once at import time (cached in memory). Validates that a submitted gene symbol is non-empty, uppercase, matches an HGNC approved symbol, and exists in the processed expression data. Returns structured result: `{valid, normalized_symbol, error_message}`.

**Cancer type validator:** Accepts only BRCA, LUAD, COAD (case-insensitive). Returns structured result.

**Combined request validator:** Runs both validators and returns all errors simultaneously rather than failing on the first.

### 4.3 Sample ID Normalizer

**File:** `backend/utils/id_normalizer.py`

Single canonical function for normalizing TCGA sample IDs to 12-character patient barcodes. Handles all known TCGA barcode formats. Imported by both preprocessing scripts and analysis modules.

### 4.4 Cache Manager

**File:** `backend/utils/cache_manager.py`

File-based cache stored in `backend/cache/`. Cache keys are deterministic strings derived from analysis type, gene, and cancer. Each entry is a JSON file containing result data and a timestamp. Checks TTL before returning cached data. Writes are atomic (write to temp file, rename). Respects the `cache_enabled` flag from config. Stores complete JSON-serializable analysis results so a cache hit bypasses all computation.

---

## Section 5 — Backend Analysis Modules

### 5.1 Expression Analysis Module

**File:** `backend/analysis/expression_analysis.py`

**Inputs:** Validated gene symbol, validated cancer type.

**Steps:**
1. Load the gene's row from the cancer's tumor and normal Parquet files using index-based row selection — do not load the full matrix.
2. Extract two 1D expression arrays (log2 TPM values): tumor and normal.
3. Compute descriptive statistics for both groups: mean, median, standard deviation, min, max, sample count.
4. Compute fold change in TPM space: convert log2 values back to TPM, divide mean tumor TPM by mean normal TPM (guard against division by zero), then compute log2 fold change.
5. Test normality with Shapiro–Wilk on a subsample of up to 5000 values per group. Run Welch's t-test if both groups are normally distributed; run Mann–Whitney U test otherwise. Record which test was used.
6. Generate a combination boxplot and violin plot using Plotly. X-axis shows both groups labeled with sample counts. Y-axis shows log2(TPM+0.001). Include a jitter overlay (subsample to 200 points per group for legibility). Annotate with p-value and test name. Serialize as Plotly JSON.

**Output contract (all fields required, no None values):**
```
{
  gene, cancer,
  tumor_count, normal_count,
  tumor_mean_log2, normal_mean_log2,
  fold_change, log2_fold_change,
  p_value, statistical_test, significant,
  direction (one of: "upregulated", "downregulated", "unchanged"),
  plot_json
}
```

Direction is "upregulated" if log2FC > 1 and p < threshold, "downregulated" if log2FC < -1 and p < threshold, otherwise "unchanged".

### 5.2 Survival Analysis Module

**File:** `backend/analysis/survival_analysis.py`

**Inputs:** Validated gene symbol, validated cancer type, split strategy string ("median" for MVP; module must be architecturally ready to accept "quartile" or "percentile" without refactoring).

**Steps:**
1. Load the gene's tumor expression vector from the tumor Parquet file.
2. Load the processed clinical survival Parquet for the cancer.
3. Normalize sample IDs in both datasets and perform an inner join. Log samples lost in the merge.
4. Split patients at the median expression value into High and Low groups.
5. Validate that both groups have at least 20 patients. Return an error result if not.
6. Fit Kaplan–Meier separately for both groups using `lifelines.KaplanMeierFitter`. Extract median survival and 95% confidence intervals.
7. Run log-rank test using `lifelines.statistics.logrank_test`. Extract test statistic and p-value.
8. Fit a univariate Cox proportional hazards model using `lifelines.CoxPHFitter` with a binary High/Low covariate. Extract hazard ratio and 95% confidence interval.
9. Generate a Plotly KM curve with two survival curves, shaded confidence interval bands, and annotations for p-value, hazard ratio with CI, and sample counts per group.

**Output contract (all fields required):**
```
{
  gene, cancer,
  high_count, low_count,
  median_survival_high, median_survival_low,
  logrank_p_value, hazard_ratio, hr_confidence_interval,
  significant, split_strategy, split_value,
  plot_json
}
```

### 5.3 Mutation Analysis Module

**File:** `backend/analysis/mutation_analysis.py`

**Inputs:** Validated gene symbol, validated cancer type.

**Steps:**
1. Load the cancer's processed mutation Parquet file. Load cohort size and baseline mutation rate from the JSON metadata file.
2. Filter for rows where `Hugo_Symbol` matches the gene. Zero mutations is a valid result, not an error.
3. Count unique mutated patients. Divide by cohort size for frequency percentage.
4. Group by standardized mutation category. Compute percentage of each type relative to total mutations in the gene.
5. Generate two Plotly figures:
   - Figure 1: Horizontal bar chart showing mutation rate with an annotation of "{X}% of {N} patients" and a reference marker for the cancer baseline rate.
   - Figure 2: Donut chart of mutation type distribution. If zero mutations, return a placeholder figure with a "No mutations detected" annotation.

**Output contract (all fields required):**
```
{
  gene, cancer, cohort_size, mutated_patients,
  mutation_frequency_percent, has_mutations,
  mutation_types: { Missense, Nonsense, Frameshift, Splice Site, In-frame Indel, Silent, Other },
  frequency_plot_json, type_plot_json
}
```

### 5.4 AI Interpretation Module

**File:** `backend/analysis/ai_summary.py`

**Inputs:** Complete expression result dict, complete survival result dict, complete mutation result dict. Validate at entry that all three are fully populated before proceeding.

**Prompt construction:** Build the prompt entirely from structured numerical data extracted from the three result dicts. Include: gene, cancer, fold change, log2FC, p-value, direction, sample counts, test used, hazard ratio with CI, logrank p-value, median survivals, mutation frequency, cohort size, most common mutation type. Instruct the model to write 3–5 sentences maximum, use only the provided statistics, state whether the gene shows evidence of prognostic biomarker relevance, use hedged language, and never mention drugs or therapies.

**API call:** Use `httpx.AsyncClient` (singleton, instantiated at app startup). Call OpenRouter `/v1/chat/completions` with 30-second timeout and one retry on failure. If the API call fails after retry, return a fallback summary constructed entirely from the statistical data using a template string — never return an error when a template can be generated.

**Output contract:**
```
{
  summary, generated_by ("ai" or "fallback_template"), model_used
}
```

---

## Section 6 — FastAPI Routes and Application

### 6.1 Application Entry Point

**File:** `backend/app.py`

Creates and configures the FastAPI application. Responsibilities:
- Run the preprocessing orchestrator on startup; halt if it fails
- Instantiate the `httpx.AsyncClient` singleton and inject it into the AI module
- Register all routers with appropriate URL prefixes
- Configure CORS: allow `http://localhost:3000` in development; configurable for production via environment variable
- Mount static files at `/reports` for PDF download access
- Register global exception handlers that return structured JSON error responses for all unhandled exceptions — never expose raw tracebacks
- Log application startup time

### 6.2 Pydantic Request and Response Models

**File:** `backend/models.py`

Define Pydantic models for all request bodies and response payloads. The `AnalysisRequest` model contains `gene` (string) and `cancer` (string). The full analysis response model contains nested objects for each of the four analysis sections plus a top-level status field, analysis metadata (gene, cancer, timestamp), and a report download URL. Each nested section can independently carry either a result payload or an error object — this allows partial success responses.

### 6.3 POST /analyze

**File:** `backend/routes/summary.py`

Master endpoint that orchestrates all four modules.

Handler order:
1. Validate request — return 422 with structured error if invalid
2. Check cache — return cached result immediately if hit
3. Run expression, survival, and mutation analyses concurrently using `asyncio.gather`. Wrap all CPU-bound operations in `run_in_executor` to avoid blocking the event loop
4. Assemble partial result regardless of individual failures. A failed module returns an error object in its section; the other modules' results are still included
5. Run AI interpretation only if at least two of three analysis modules succeeded
6. Assemble unified response
7. Write to cache
8. Trigger PDF report generation as a background task (client does not wait for this)
9. Return unified response

### 6.4 POST /expression, POST /survival, POST /mutation

**Files:** `backend/routes/expression.py`, `backend/routes/survival.py`, `backend/routes/mutation.py`

Individual endpoints for each analysis module. Apply caching. Return the module's output contract directly. These allow the frontend to re-run individual sections without triggering all four modules.

### 6.5 GET /validate

Query parameters: `gene`, `cancer`. Returns validation result for real-time frontend input validation. Not cached.

### 6.6 GET /genes

Returns the complete list of gene symbols from the gene index file as a JSON array. Loaded once at startup and kept in memory. Used by the frontend for autocomplete.

### 6.7 GET /health

Returns server status, preprocessing completion status, and timestamp. Used by deployment infrastructure and the frontend's status indicator.

---

## Section 7 — Report Generation

**File:** `backend/utils/report_generator.py`

Generates downloadable PDF reports from complete analysis results. Implementation approach: use Plotly's `kaleido` static image export to render each plot as a high-resolution PNG, then assemble everything into a PDF using `reportlab`.

**Report structure:**
1. Cover page: gene name, cancer type, analysis date, dataset sources
2. Expression section: violin/boxplot PNG + numeric table (fold change, p-value, sample counts, test used)
3. Survival section: KM curve PNG + numeric table (HR, CI, p-value, median survivals)
4. Mutation section: both mutation plot PNGs + numeric table (frequency, cohort size, type breakdown)
5. AI interpretation section: summary text in a styled block, labeled with whether it was AI-generated or template-generated
6. Data sources section: formatted citations for UCSC Xena (expression, clinical) and cBioPortal (mutation)

**File naming:** `{GENE}_{CANCER}_{timestamp}.pdf` stored in `backend/reports/`. The report URL in the API response points to `/reports/{filename}`.

Report generation runs asynchronously. If it fails, log the error and do not surface it to the client.

---

## Section 8 — Error Handling Specification

Every error returned by any endpoint must follow this structure:
```
{ "error": true, "error_code": string, "message": string, "details": object or null }
```

| Error Code | Meaning |
|---|---|
| `INVALID_GENE` | Gene symbol not found in HGNC or not in dataset |
| `INVALID_CANCER` | Cancer type not in supported list |
| `INSUFFICIENT_SAMPLES` | Too few samples for reliable analysis |
| `MERGE_FAILURE` | Expression and clinical data could not be joined |
| `STATISTICAL_FAILURE` | Statistical test raised an exception |
| `AI_UNAVAILABLE` | OpenRouter API failed and fallback template was used |
| `PREPROCESSING_INCOMPLETE` | Required processed data file is missing |
| `CACHE_ERROR` | Cache read/write failed (non-fatal, log and continue) |

Never return a raw Python exception traceback in an API response. Log the traceback internally.

---

## Section 9 — Backend Testing Requirements

### 9.1 Test Fixtures

Create small deterministic synthetic datasets in `backend/tests/fixtures/` (seeded random numbers):
- Expression Parquet: 50 genes × 30 tumor + 15 normal samples
- Clinical Parquet: 30 patients with survival data
- Mutation Parquet: several hundred rows across known gene symbols

### 9.2 Required Tests

**Expression:** Correct fold change for a known synthetic case; correct test selection based on distribution; fully populated output contract; graceful handling of gene not found.

**Survival:** Median split produces balanced groups; KM and log-rank run without error; hazard ratio extracted correctly; error result returned when group has fewer than 20 patients.

**Mutation:** Frequency normalization by cohort size; zero-mutation gene returns valid result; mutation type categorization mapping is complete.

**Validators:** Invalid genes rejected; valid genes pass; cancer type validation is case-insensitive; combined validator returns all errors simultaneously.

### 9.3 Test Execution

```
pytest backend/tests/ -v --tb=short
```

All tests must pass before the implementation is considered complete.

---

## Section 10 — Backend Performance Rules

**Never load the full expression matrix during analysis.** Parquet row selection by gene symbol index is the only permitted access pattern during analysis.

**Use connection pooling for the OpenRouter HTTP client.** Instantiate `httpx.AsyncClient` once at startup and reuse it.

**Set Pandas copy-on-write behavior globally.** Enable after Pandas 2.0 to avoid silent data mutation bugs.

**Monitor memory during preprocessing.** Delete each chunk object after processing and call garbage collection.

**Never block the FastAPI event loop.** Wrap all Pandas, NumPy, SciPy, and Lifelines operations in `loop.run_in_executor(None, sync_function)`.

---

## Section 11 — Frontend Architecture

### 11.1 Design Philosophy

The frontend must feel like a professional scientific research tool. The aesthetic is: dark-themed, data-dense, clinically precise. Think genomics browser meets medical dashboard — not a startup landing page.

**Visual identity:**
- Background: deep charcoal (`#0f1117`) with subtle panel contrast (`#161b22`)
- Primary accent: a cool teal (`#00c9a7`) for active states, highlights, and significance indicators
- Danger/warning: muted amber (`#f0a500`) for insignificant p-values and warnings
- Error: muted crimson (`#c0392b`) for failed module states
- Typography: a monospaced or technical serif for gene names and numeric values; a clean sans-serif for body text. Never use default system fonts
- All panels have a subtle border (`1px solid #2a2f3a`) and a very slight border-radius (4px) — scientific, not bubbly
- No gradients except as very subtle background texture on the main header

**Layout:** The dashboard is a single-page layout. There is no horizontal scrolling. The search controls sit in a fixed top bar. The four analysis panels stack vertically below it in a single-column layout on the main content area. On wider viewports (>1200px), expression and survival panels can sit side by side in a two-column grid. Mutation panels (two charts) always sit side by side within their section.

### 11.2 State Management

**File:** `frontend/src/state/analysisContext.js` and `frontend/src/state/analysisReducer.js`

Use React Context and `useReducer` for all application state. Do not use component-level state for anything that needs to be shared across panels.

**State shape:**
```
{
  query: { gene: string, cancer: string },
  status: "idle" | "loading" | "partial" | "complete" | "error",
  results: {
    expression: { status: "idle"|"loading"|"success"|"error", data: object|null, error: object|null },
    survival:   { status: "idle"|"loading"|"success"|"error", data: object|null, error: object|null },
    mutation:   { status: "idle"|"loading"|"success"|"error", data: object|null, error: object|null },
    interpretation: { status: "idle"|"loading"|"success"|"error", data: object|null, error: object|null }
  },
  reportUrl: string|null,
  lastAnalyzedAt: string|null
}
```

**Reducer actions:**
- `ANALYSIS_START` — set status to "loading", clear all previous results
- `ANALYSIS_SUCCESS` — populate all result sections from the API response
- `ANALYSIS_PARTIAL` — populate available sections, mark failed sections with error status
- `ANALYSIS_ERROR` — set top-level status to "error", store error
- `SECTION_ERROR` — mark a specific section as errored without affecting others
- `REPORT_READY` — store the report URL
- `RESET` — return to idle state

### 11.3 Service Layer

**File:** `frontend/src/services/api.js`

Create a single configured `axios` instance with:
- `baseURL` set from `config.js`
- Default headers including `Content-Type: application/json`
- A request interceptor that logs outgoing requests in development mode
- A response interceptor that normalizes error responses into a consistent shape regardless of HTTP status code — the rest of the application never deals with raw Axios errors

**File:** `frontend/src/services/analysisService.js`

Wraps API calls for analysis. Exports:
- `runFullAnalysis(gene, cancer)` — calls `POST /analyze`, returns the full result object
- `runExpressionAnalysis(gene, cancer)` — calls `POST /expression`
- `runSurvivalAnalysis(gene, cancer)` — calls `POST /survival`
- `runMutationAnalysis(gene, cancer)` — calls `POST /mutation`

Each function handles its own error normalization and never throws raw HTTP errors upward. Returns a result object with `{ success: boolean, data: object|null, error: object|null }`.

**File:** `frontend/src/services/geneService.js`

Wraps gene-related API calls. Exports:
- `fetchGeneList()` — calls `GET /genes`, returns array of gene symbols; caches the result in module-level memory so it is only fetched once per session
- `validateGene(gene, cancer)` — calls `GET /validate` with query params, returns validation result

### 11.4 Custom Hooks

**File:** `frontend/src/hooks/useAnalysis.js`

Encapsulates the full analysis flow. Consumes the analysis context. Exposes:
- `runAnalysis(gene, cancer)` — dispatches `ANALYSIS_START`, calls `runFullAnalysis`, dispatches `ANALYSIS_SUCCESS` or `ANALYSIS_PARTIAL` based on which sections succeeded
- `resetAnalysis()` — dispatches `RESET`
- The current `status` and `results` from context

Components never call the service layer directly — they always go through this hook.

**File:** `frontend/src/hooks/useGeneAutocomplete.js`

Manages gene search autocomplete behavior. Responsibilities:
- Calls `geneService.fetchGeneList()` on first invocation and caches the list
- Filters the gene list locally based on the current input string (client-side filtering — no API call per keystroke)
- Returns `{ suggestions: string[], loading: boolean }`
- Filters are case-insensitive and match from the beginning of the gene symbol
- Limit suggestions to the top 10 matches

---

## Section 12 — Frontend Components

Build components in the order: shared utilities first, then layout, then search, then analysis panels.

### 12.1 Shared Utility Components

**StatCard** (`frontend/src/components/shared/StatCard.js`)

A reusable card for displaying a single metric. Props: `label` (string), `value` (string or number), `unit` (optional string), `significance` (optional: "significant", "not-significant", "neutral"). When `significance` is "significant", render the value in the teal accent color. When "not-significant", render in amber. Neutral renders in the default text color. Always display the label in a smaller, muted font above the value.

**SectionPanel** (`frontend/src/components/shared/SectionPanel.js`)

A reusable container for each analysis section. Props: `title` (string), `status` ("idle" | "loading" | "success" | "error"), `children`. When status is "loading", render a `LoadingOverlay` that covers the panel content area. When status is "error", render an `ErrorBlock` in place of children. When status is "idle", render a muted placeholder message. When status is "success", render children normally.

**LoadingOverlay** (`frontend/src/components/shared/LoadingOverlay.js`)

A semi-transparent overlay with a pulsing animation — not a spinning circle. Use a horizontal scanning line or a DNA-helix-inspired shimmer that fits the scientific theme. The overlay text says "Analyzing..." followed by the section name.

**ErrorBlock** (`frontend/src/components/shared/ErrorBlock.js`)

Props: `errorCode` (string), `message` (string), `details` (optional object). Renders the error code in a monospaced font in muted crimson. The message is displayed in normal body text below it. If details are provided, render them in a collapsed expandable section (implemented with a simple toggle — no library). Never show a blank white box.

**Badge** (`frontend/src/components/shared/Badge.js`)

A small inline label for significance, direction, or mutation status. Props: `type` ("significant" | "not-significant" | "upregulated" | "downregulated" | "unchanged" | "mutated" | "not-mutated"), `label` (string). Each type has a distinct color: significant/upregulated → teal, downregulated → muted blue, not-significant/unchanged → amber, mutated → orange, not-mutated → gray.

**DownloadButton** (`frontend/src/components/shared/DownloadButton.js`)

Props: `url` (string | null), `label` (string), `disabled` (boolean). When `url` is null or `disabled` is true, renders as a muted, non-clickable button. When active, clicking triggers a file download by opening the URL. Shows a small download icon before the label text (use an inline SVG icon — no icon library).

### 12.2 Layout Components

**AppShell** (`frontend/src/components/layout/AppShell.js`)

The root layout wrapper. Contains `TopBar` and the main content area. Sets the dark background color and the global font. Manages the overall page grid: top bar is fixed, content area scrolls independently.

**TopBar** (`frontend/src/components/layout/TopBar.js`)

Fixed top bar containing:
- Application name "Cancer Gene Validation Copilot" on the left in the technical display font
- A small version badge
- Navigation links to the Dashboard and About pages on the right
- A subtle bottom border to separate it from the content area

The TopBar does not scroll with the page content.

**Sidebar** (`frontend/src/components/layout/Sidebar.js`)

On viewports wider than 1400px, a narrow left sidebar (220px) displays a quick-reference key for the current analysis: gene name, cancer type, analysis timestamp, and a color-coded significance legend. On narrower viewports it is hidden. This is a supplementary information panel, not a navigation sidebar.

### 12.3 Search Components

**GeneSearchBar** (`frontend/src/components/search/GeneSearchBar.js`)

The primary gene input. Responsibilities:
- Text input field with the placeholder "Enter gene symbol (e.g. TP53)"
- Real-time filtering using `useGeneAutocomplete` hook
- Autocomplete dropdown: renders below the input, shows up to 10 gene symbol suggestions, keyboard-navigable (arrow keys, Enter to select, Escape to close)
- Each suggestion item is a clickable row showing the gene symbol in monospaced font
- When the user selects a suggestion or blurs the field, call `geneService.validateGene` and display an inline validation indicator: a green checkmark for valid, a red X with the error message for invalid
- The submit action is only enabled when both gene and cancer are valid
- Clear button (×) appears when the input has a value

**CancerSelector** (`frontend/src/components/search/CancerSelector.js`)

Three selectable cancer type cards displayed in a horizontal row. Each card shows the cancer full name and its TCGA code. Clicking a card selects it (highlighted with the teal accent border). Only one can be selected at a time. Cards are not radio buttons styled as buttons — they are actual styled div elements that communicate selection state visually through border, background tint, and the TCGA code label appearing in accent color.

### 12.4 Summary Metrics Bar

**SummaryMetricsBar** (`frontend/src/components/metrics/SummaryMetricsBar.js`)

A horizontal bar of `StatCard` components that appears between the search controls and the analysis panels once results are available. Always hidden in idle state.

Contains four cards in this order:
1. **Log2 Fold Change** — from expression results. Value shown with +/- sign. Significance determined by the expression module's `significant` field
2. **Hazard Ratio** — from survival results, shown with 95% CI in smaller text below
3. **Mutation Frequency** — from mutation results, shown as a percentage
4. **AI Summary Status** — shows "AI Interpreted" or "Template Generated" as a badge depending on `generated_by` field

If any module's data is unavailable (error state), its card renders in a muted "N/A" state rather than being hidden.

### 12.5 Expression Panel

**ExpressionPanel** (`frontend/src/components/expression/ExpressionPanel.js`)

Wraps everything in a `SectionPanel` with title "Differential Expression Analysis". When in success state, renders:
- A row of three `StatCard` components: Fold Change, p-value, and statistical test used
- A `Badge` showing direction ("Upregulated", "Downregulated", or "Unchanged")
- The `ExpressionPlot` component

**ExpressionPlot** (`frontend/src/components/expression/ExpressionPlot.js`)

Renders the Plotly JSON received from the backend using `react-plotly.js`. Props: `plotJson` (the Plotly figure JSON object). The component applies a consistent dark-mode Plotly layout config (dark background, light text, grid lines matching the panel border color) on top of the backend-generated figure data. This dark-mode theming is applied by the component, not by the backend — the backend sends neutral layout, the frontend applies the theme. The plot must be fully responsive: use `useLayout: true` and `responsive: true` in the Plotly config. Do not hardcode pixel widths.

### 12.6 Survival Panel

**SurvivalPanel** (`frontend/src/components/survival/SurvivalPanel.js`)

Wraps in a `SectionPanel` with title "Survival Analysis". When in success state, renders:
- A row of `StatCard` components: Hazard Ratio, log-rank p-value, median survival (High group), median survival (Low group)
- A `Badge` for significance
- The `SurvivalPlot` component

**SurvivalPlot** (`frontend/src/components/survival/SurvivalPlot.js`)

Same rendering approach as ExpressionPlot. Apply the same dark-mode Plotly theme. Ensure confidence interval shaded areas use semi-transparent fills compatible with the dark background.

### 12.7 Mutation Panel

**MutationPanel** (`frontend/src/components/mutation/MutationPanel.js`)

Wraps in a `SectionPanel` with title "Mutation Profiling". When in success state, renders:
- A `StatCard` showing mutation frequency with a `Badge` ("Mutated" or "Not Detected")
- A `StatCard` showing cohort size
- A two-column grid containing `MutationFrequencyPlot` on the left and `MutationTypePlot` on the right
- A breakdown table of mutation types beneath the plots (a plain HTML table, styled with CSS — no table library)

**MutationFrequencyPlot** and **MutationTypePlot**: Same rendering approach as ExpressionPlot with dark-mode Plotly theme applied.

### 12.8 AI Interpretation Panel

**AIInterpretationPanel** (`frontend/src/components/interpretation/AIInterpretationPanel.js`)

Wraps in a `SectionPanel` with title "AI Scientific Interpretation". When in success state, renders:
- A model/source badge: "OpenRouter AI" or "Statistical Template" depending on `generated_by`
- The summary text in a styled blockquote-like container with a left border in the teal accent color
- A small italic disclaimer below the text: "This interpretation is generated from statistical data only and should not be used as clinical guidance."

### 12.9 Dashboard Page

**DashboardPage** (`frontend/src/pages/DashboardPage.js`)

Assembles the full analysis dashboard. Layout from top to bottom:
1. Search area: `GeneSearchBar`, `CancerSelector`, and a prominent "Run Analysis" button
2. `SummaryMetricsBar` (hidden until results arrive)
3. `ExpressionPanel`
4. `SurvivalPanel`
5. `MutationPanel`
6. `AIInterpretationPanel`
7. A report download row containing a `DownloadButton` for the PDF report

The "Run Analysis" button dispatches the analysis through `useAnalysis`. It shows a loading state (disabled, with an animated indicator) while the request is in flight. It returns to its default state when the request completes regardless of outcome.

All six analysis panels are always rendered in the DOM once the page loads. They begin in "idle" state and transition through "loading" to "success" or "error" as results arrive. Panels do not mount and unmount — they always exist and respond to state changes.

### 12.10 About Page

**AboutPage** (`frontend/src/pages/AboutPage.js`)

A static informational page. Contains:
- Project overview: what the platform does, what it does not do
- Data sources section: descriptions and links to UCSC Xena and cBioPortal
- Supported analyses section: a summary of each of the four analysis types
- Statistical methods section: which tests are used and when
- Limitations section: minimum sample requirements, supported cancer types, the fact that results are exploratory and not clinically validated

This page has no dynamic content and makes no API calls.

### 12.11 App Router

**App.js** (`frontend/src/App.js`)

Sets up React Router with two routes:
- `/` → `DashboardPage`
- `/about` → `AboutPage`

Wraps both routes with `AppShell` and the `AnalysisContext.Provider`.

---

## Section 13 — Frontend Styling

### 13.1 CSS Architecture

All styles are written in plain CSS3. Do not use CSS modules, styled-components, or any CSS-in-JS approach. Use four files:

**`variables.css`** — defines all CSS custom properties (variables):
- Color palette (all background, surface, border, text, and accent colors)
- Typography scale (font families, sizes, weights, line heights)
- Spacing scale (a consistent set of spacing values: 4px, 8px, 12px, 16px, 24px, 32px, 48px)
- Border radius values
- Transition durations
- Shadow definitions

Every other CSS file must only reference values from `variables.css` — no hardcoded colors, sizes, or font names anywhere else.

**`typography.css`** — defines all text styles: headings, body text, monospaced values, labels, captions, and gene/cancer name display styles. Import the chosen fonts from Google Fonts in this file.

**`global.css`** — imports `variables.css` and `typography.css`. Sets box-sizing, resets margins, sets the body background and font, and defines utility classes (`.visually-hidden`, `.truncate`, `.monospace`). This is imported once in `index.js`.

**`components.css`** — all component-specific styles organized with clear section comments. Each component's styles are grouped and labeled. Avoid deeply nested selectors — maximum two levels of nesting.

### 13.2 Responsive Breakpoints

Define breakpoints in `variables.css` and use them consistently in `components.css`:
- Narrow (mobile): below 768px — single column, search controls stack vertically
- Medium (tablet): 768px–1199px — single column, search controls in a row
- Wide (desktop): 1200px and above — expression and survival panels side by side
- Extra wide: 1400px and above — sidebar becomes visible

### 13.3 Animation and Interaction States

Define all transition durations as CSS variables. Use them for:
- Button hover and active states (subtle background shift, 150ms)
- Panel loading shimmer animation (CSS keyframe, not a library)
- Autocomplete dropdown slide-in (CSS transform + opacity, 100ms)
- Cancer selector card selection state change (border and background, 150ms)

No animation should feel slow or decorative — every transition serves a functional purpose (indicating state change).

---

## Section 14 — Frontend Testing Requirements

### 14.1 Service Tests

**`analysisService.test.js`:**
- Test that `runFullAnalysis` calls the correct endpoint with correct parameters
- Test that a successful response returns `{ success: true, data: ... }`
- Test that a failed response returns `{ success: false, error: ... }` without throwing
- Test that a partial success (some sections failed) is handled correctly

**`geneService.test.js`:**
- Test that `fetchGeneList` returns an array of strings
- Test that the gene list is cached after the first call (second call does not make a network request)
- Test that `validateGene` returns correct structure for valid and invalid inputs

### 14.2 Component Tests

**`GeneSearchBar.test.js`:**
- Test that the input renders with the correct placeholder
- Test that typing triggers autocomplete suggestion population
- Test that selecting a suggestion updates the input value
- Test that the clear button clears the input

**`SummaryMetricsBar.test.js`:**
- Test that the bar is not rendered in idle state
- Test that the bar renders with correct values when results are provided
- Test that the N/A state renders correctly for a failed module

### 14.3 Test Execution

```
cd frontend && npm test -- --watchAll=false
```

All tests must pass before the implementation is considered complete.

---

## Section 15 — Full-Stack Integration Rules

**Plotly JSON compatibility:** The backend serializes Plotly figures using `plotly.io.to_json()`. The frontend must parse this string back into a JavaScript object before passing it to `react-plotly.js`. This parsing happens inside the plot components — the Redux/Context store holds the raw JSON string.

**Dark mode theming of Plotly plots:** The backend generates Plotly figures with a neutral (white/light) layout. The frontend plot components override the layout template on the client side by merging a dark layout configuration into the figure before rendering. This means the backend never needs to know about the frontend's color scheme. Plotly's `layout.paper_bgcolor`, `layout.plot_bgcolor`, `layout.font.color`, `layout.xaxis.gridcolor`, and `layout.yaxis.gridcolor` are all overridden by the frontend component.

**Partial success handling:** The `POST /analyze` endpoint can return a response where some sections have succeeded and others have errored. The frontend reducer handles this by setting each section's status independently. The dispatcher must inspect each section of the response individually, not assume that a 200 HTTP status means all sections succeeded.

**Gene autocomplete performance:** The gene list from `GET /genes` may contain tens of thousands of symbols. The filtering in `useGeneAutocomplete` must be fast. Use a simple `startsWith` comparison on the uppercased input string — this is O(n) but fast enough for client-side filtering at this scale. Do not use fuzzy matching — gene symbols require exact prefix matching for scientific accuracy.

**Report download timing:** The PDF report is generated asynchronously after the API response is returned. The `reportUrl` field in the initial response may be null. The `DownloadButton` renders as disabled when `reportUrl` is null. If the backend implementation supports a status poll endpoint for report generation, the frontend `useAnalysis` hook polls every 5 seconds until the URL becomes available. If polling is not implemented, the button remains disabled and shows the label "Report generating..." until the next analysis is run.

**CORS in development:** The backend allows `http://localhost:3000`. The frontend `package.json` must include a proxy configuration: `"proxy": "http://localhost:8000"` so that development API calls are correctly routed.

---

## Section 16 — Implementation Sequence (Agent Execution Order)

Execute these phases strictly in order. Do not begin a phase until every checklist item in the previous phase is marked complete.

### Phase 1 — Project Foundation
- [ ] Create complete directory structure for both backend and frontend
- [ ] Write `backend/requirements.txt` with pinned versions
- [ ] Write `frontend/package.json` with pinned versions
- [ ] Write `backend/config.py` fully
- [ ] Write `frontend/src/config.js` fully
- [ ] Write `backend/.env.example` with all required environment variable names
- [ ] Write `frontend/.env.example` with all required environment variable names

### Phase 2 — Backend Utilities
- [ ] Write `backend/utils/logger.py`
- [ ] Write `backend/utils/id_normalizer.py`
- [ ] Write `backend/utils/validators.py`
- [ ] Write `backend/utils/cache_manager.py`

### Phase 3 — Preprocessing Pipeline
- [ ] Write `backend/preprocessing/preprocess_expression.py`
- [ ] Write `backend/preprocessing/preprocess_clinical.py`
- [ ] Write `backend/preprocessing/preprocess_mutation.py`
- [ ] Write `backend/preprocessing/run_all.py`
- [ ] Verify all scripts are idempotent
- [ ] Verify output file names and formats match the specification exactly

### Phase 4 — Backend Analysis Modules
- [ ] Write `backend/analysis/expression_analysis.py` fully
- [ ] Write `backend/analysis/survival_analysis.py` fully
- [ ] Write `backend/analysis/mutation_analysis.py` fully
- [ ] Write `backend/analysis/ai_summary.py` fully including fallback template
- [ ] Verify all output contracts are fully populated with no None values

### Phase 5 — Backend Tests
- [ ] Create all synthetic test fixtures in `backend/tests/fixtures/`
- [ ] Write `backend/tests/test_expression.py`
- [ ] Write `backend/tests/test_survival.py`
- [ ] Write `backend/tests/test_mutation.py`
- [ ] Write `backend/tests/test_validators.py`
- [ ] Run `pytest backend/tests/ -v --tb=short` — all must pass

### Phase 6 — Backend API Layer
- [ ] Write `backend/models.py` with all Pydantic models
- [ ] Write `backend/routes/expression.py`
- [ ] Write `backend/routes/survival.py`
- [ ] Write `backend/routes/mutation.py`
- [ ] Write `backend/routes/summary.py`
- [ ] Write `backend/utils/report_generator.py`
- [ ] Write `backend/app.py` with startup routine, CORS, static files, and exception handlers

### Phase 7 — Backend Integration Verification
- [ ] Start server: `uvicorn backend.app:app --reload`
- [ ] `GET /health` returns 200 with preprocessing status
- [ ] `GET /genes` returns a populated array
- [ ] `GET /validate?gene=TP53&cancer=BRCA` returns `valid: true`
- [ ] `POST /analyze` with `{"gene": "TP53", "cancer": "BRCA"}` returns all four sections populated
- [ ] `POST /analyze` with invalid gene returns structured error with `INVALID_GENE` code
- [ ] Second identical `POST /analyze` returns from cache (confirm in logs)
- [ ] PDF file appears in `backend/reports/` after a successful analysis
- [ ] `GET /reports/{filename}` successfully downloads the PDF

### Phase 8 — Frontend Foundation
- [ ] Install all frontend dependencies: `cd frontend && npm install`
- [ ] Write `frontend/src/styles/variables.css` with complete design token set
- [ ] Write `frontend/src/styles/typography.css` with all text styles and font imports
- [ ] Write `frontend/src/styles/global.css`
- [ ] Write `frontend/src/styles/components.css` (initially empty, filled in as components are built)
- [ ] Write `frontend/src/config.js`
- [ ] Write `frontend/src/state/analysisReducer.js` with all actions and state transitions
- [ ] Write `frontend/src/state/analysisContext.js`

### Phase 9 — Frontend Service Layer
- [ ] Write `frontend/src/services/api.js` with axios instance, interceptors
- [ ] Write `frontend/src/services/analysisService.js` with all four service functions
- [ ] Write `frontend/src/services/geneService.js` with gene list caching and validation

### Phase 10 — Frontend Custom Hooks
- [ ] Write `frontend/src/hooks/useAnalysis.js`
- [ ] Write `frontend/src/hooks/useGeneAutocomplete.js`

### Phase 11 — Shared Components
- [ ] Write and style `StatCard`
- [ ] Write and style `SectionPanel`
- [ ] Write and style `LoadingOverlay`
- [ ] Write and style `ErrorBlock`
- [ ] Write and style `Badge`
- [ ] Write and style `DownloadButton`

### Phase 12 — Layout Components
- [ ] Write and style `AppShell`
- [ ] Write and style `TopBar`
- [ ] Write and style `Sidebar`

### Phase 13 — Search Components
- [ ] Write and style `GeneSearchBar` with full autocomplete behavior
- [ ] Write and style `CancerSelector` with card-based selection

### Phase 14 — Analysis Panel Components
- [ ] Write and style `ExpressionPlot` with dark-mode Plotly theming
- [ ] Write and style `ExpressionPanel` with stat cards and badge
- [ ] Write and style `SurvivalPlot` with dark-mode Plotly theming
- [ ] Write and style `SurvivalPanel` with stat cards and badge
- [ ] Write and style `MutationFrequencyPlot`
- [ ] Write and style `MutationTypePlot`
- [ ] Write and style `MutationPanel` with mutation type table
- [ ] Write and style `AIInterpretationPanel` with source badge and disclaimer

### Phase 15 — Metrics and Page Assembly
- [ ] Write and style `SummaryMetricsBar`
- [ ] Write `DashboardPage` assembling all components
- [ ] Write `AboutPage` with all required content
- [ ] Write `App.js` with router and context provider setup
- [ ] Write `frontend/src/index.js`
- [ ] Write `frontend/public/index.html` with correct title and meta tags

### Phase 16 — Frontend Tests
- [ ] Write `frontend/src/tests/services/analysisService.test.js`
- [ ] Write `frontend/src/tests/services/geneService.test.js`
- [ ] Write `frontend/src/tests/components/GeneSearchBar.test.js`
- [ ] Write `frontend/src/tests/components/SummaryMetricsBar.test.js`
- [ ] Run `cd frontend && npm test -- --watchAll=false` — all must pass

### Phase 17 — Full-Stack Integration Verification
- [ ] Start backend: `uvicorn backend.app:app --reload`
- [ ] Start frontend: `cd frontend && npm start`
- [ ] Application loads at `http://localhost:3000` with correct dark theme and typography
- [ ] Gene search bar renders with placeholder; typing "TP" shows gene suggestions
- [ ] Selecting a gene symbol from autocomplete populates the input and shows green validation indicator
- [ ] Selecting "BRCA" cancer type card highlights it with accent border
- [ ] Clicking "Run Analysis" shows loading overlays on all four panels simultaneously
- [ ] Expression panel populates with correct fold change, p-value, and interactive Plotly chart in dark theme
- [ ] Survival panel populates with hazard ratio, KM curve in dark theme with confidence intervals
- [ ] Mutation panel populates with frequency bar and donut chart
- [ ] AI Interpretation panel populates with summary text and source badge
- [ ] Summary metrics bar appears between search and panels with correct values
- [ ] Running analysis for an invalid gene shows inline validation error before submitting
- [ ] Download button becomes active after report generation; clicking it downloads the PDF
- [ ] Navigating to `/about` renders the About page with full content
- [ ] Navigating back to `/` retains the last analysis results in state
- [ ] Running the same analysis a second time is noticeably faster (cache hit)
- [ ] On viewport width 1200px+, expression and survival panels appear side by side
- [ ] On viewport width below 768px, layout stacks correctly and is usable

### Phase 18 — Final Checks
- [ ] Run full backend test suite: all pass
- [ ] Run full frontend test suite: all pass
- [ ] Verify no hardcoded values outside `config.py` (backend) or `config.js` (frontend)
- [ ] Verify all log messages are informative and correctly leveled
- [ ] Verify all six analysis panels handle their error state visibly (test by temporarily breaking a route)
- [ ] Verify the partial success case: if survival analysis fails, expression and mutation still render
- [ ] Verify Plotly plots are responsive (resize browser window — charts reflow)
- [ ] Write complete `README.md`

---

## Section 17 — README Requirements

The `README.md` must document:

1. Project overview: what the platform is, what it does, what it is not (not clinical, exploratory only)
2. Architecture overview: a text diagram showing the data flow from datasets through backend to frontend
3. Data acquisition: exact steps to download each dataset with source URLs and expected file names and locations
4. Backend setup: Python environment creation, dependency installation, `.env` configuration
5. Frontend setup: Node.js version requirement, `npm install`, `.env` configuration
6. Running preprocessing: the command, expected output, and how to verify success
7. Running the backend: the command and the URL to access the auto-generated Swagger docs at `/docs`
8. Running the frontend: the command and the URL
9. API reference: each endpoint with request format and response format
10. Running tests: both backend and frontend commands with expected output
11. Limitations and constraints: supported cancers, minimum sample requirements, exploratory-only disclaimer, dependency on local preprocessed data

---

*End of Blueprint. The agent now has everything needed to implement a fully finished, production-ready Cancer Gene Validation Copilot — backend and frontend. Begin with Phase 1.*
