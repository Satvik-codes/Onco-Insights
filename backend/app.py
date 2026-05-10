from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.routes import expression, survival, mutation, summary
from backend.utils.logger import StructuredLogger
from backend.utils.validators import HGNC_SYMBOLS
import backend.preprocessing.run_all as preprocessing_runner
import httpx
import os
from datetime import datetime

logger = StructuredLogger(__name__)

app = FastAPI(title="Cancer Gene Validation Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": True, "error_code": "INTERNAL_ERROR", "message": "An internal server error occurred."}
    )

# Routers
app.include_router(summary.router)
app.include_router(expression.router)
app.include_router(survival.router)
app.include_router(mutation.router)

from backend.config import REPORTS_DIR
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    
    # Run preprocessing if needed
    try:
        preprocessing_runner.run_all()
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}", exc_info=True)
        # raise e
        
    logger.info("Application started successfully.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/validate")
async def validate_gene_route(gene: str, cancer: str):
    from backend.utils.validators import validate_analysis_request
    valid, norm, norm_cancer, errors = validate_analysis_request(gene, cancer)
    if not valid:
        error_messages = [e["message"] for e in errors]
        return {"valid": False, "error_message": "; ".join(error_messages)}
    return {"valid": True, "normalized_symbol": norm}

@app.get("/genes")
async def get_genes():
    from backend.utils.validators import PROCESSED_GENES
    return list(PROCESSED_GENES)

