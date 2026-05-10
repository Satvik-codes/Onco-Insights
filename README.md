# Cancer Gene Validation Copilot

## 1. Project Overview
The Cancer Gene Validation Copilot is a full-stack, AI-powered exploratory bioinformatics tool. It allows researchers to evaluate the potential of specific genes as prognostic biomarkers across major cancer types (e.g., Breast, Lung, Colon). 

**Disclaimer:** This platform is for exploratory research purposes only. It is not clinically validated and should not be used for medical diagnosis, treatment planning, or clinical decision-making.

## 2. Architecture Overview
```text
[ UCSC Xena / cBioPortal ]  <-- (Manual Download)
        │
[ Local Raw Data ]
        │
[ Preprocessing Pipeline ]  <-- (Clean, join, normalize IDs)
        │
[ Processed Parquet Data ]
        │
[ FastAPI Backend ]         <-- (Expression, Survival, Mutation modules + AI Interpretation via OpenRouter)
        │
[ React Frontend ]          <-- (Search, Status, Interactive Plotly Visualizations)
```

## 3. Data Acquisition
All data must be downloaded manually before starting the app.
- **Expression:** Download `TcgaTargetGtex_rsem_gene_tpm` from UCSC Xena's TCGA TARGET GTEx study, along with its phenotype file. Place in `backend/data/raw/expression/`.
- **Clinical:** Download TCGA Pan-Cancer clinical data from UCSC Xena. Place in `backend/data/raw/clinical/`.
- **Mutation:** Download TCGA BRCA, LUAD, and COAD mutation data (MAF files) from cBioPortal. Place in `backend/data/raw/mutation/`.
- **HGNC Reference:** Download approved gene symbol list from HGNC. Place in `backend/data/raw/hgnc_approved_symbols.txt`.

## 4. Backend Setup
Requires Python 3.10+.
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OpenRouter API key
```

## 5. Frontend Setup
Requires Node.js 18+.
```bash
cd frontend
npm install
cp .env.example .env
```

## 6. Running Preprocessing
Before running the backend for the first time, clean the downloaded data. Run this from the project root:
```bash
python -m backend.preprocessing.run_all
```
This is an idempotent script. You will see Parquet files generated in `backend/data/processed/`.

## 7. Running the Backend
From the project root, run:
```bash
python -m uvicorn backend.app:app --reload
```
Swagger UI docs available at `http://localhost:8000/docs`.

## 8. Running the Frontend
```bash
cd frontend
npm start
```
The dashboard is accessible at `http://localhost:3000`.

## 9. API Reference
- `POST /analyze`: Main endpoint. Takes `{"gene": "TP53", "cancer": "BRCA"}`. Returns a unified JSON response with expression, survival, mutation, and AI summary data.
- `POST /expression`: Run only differential expression.
- `POST /survival`: Run only survival analysis.
- `POST /mutation`: Run only mutation profiling.
- `GET /validate?gene=...&cancer=...`: Validates inputs.
- `GET /genes`: Returns available gene list.

## 10. Running Tests
**Backend Tests:**
```bash
cd backend
pytest tests/ -v --tb=short
```

**Frontend Tests:**
```bash
cd frontend
npm test -- --watchAll=false
```

## 11. Limitations and Constraints
- Supported Cancers: Only Breast Invasive Carcinoma (BRCA), Lung Adenocarcinoma (LUAD), and Colon Adenocarcinoma (COAD) are supported.
- Minimum Sample Requirements: 50 tumor samples, 10 normal samples. Analysis will log warnings or fail if sample count is too low.
- Local Data Dependency: The app does not query public APIs at runtime (except for OpenRouter for AI summaries). It relies entirely on pre-downloaded, localized data.
