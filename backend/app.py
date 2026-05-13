from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.routes import expression, survival, mutation, summary
from backend.utils.logger import StructuredLogger
from backend.utils.validators import validate_analysis_request
import backend.preprocessing.run_all as preprocessing_runner
import httpx
import os
import gc
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
    """
    Memory-safe startup:
    - Runs preprocessing only if needed (skips if already processed)
    - Does NOT preload any datasets into memory
    - Forces GC after preprocessing to release any temporary memory
    - Logs memory state for debugging on Render
    """
    from backend.utils.memory import log_memory, get_memory_usage_current_mb, force_gc

    logger.info("Starting application...")
    log_memory("startup_before")

    # Run preprocessing if needed (lazy — skips if already processed)
    try:
        preprocessing_runner.run_all()
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}", exc_info=True)

    # Force GC after preprocessing to release any build-up memory
    force_gc()
    log_memory("startup_after_gc")

    # Log initial memory state for Render debugging
    current_mb = get_memory_usage_current_mb()
    logger.info(f"Startup complete. Memory after startup: {current_mb:.1f}MB")

    if current_mb > 200:
        logger.warning(
            f"Startup memory is high ({current_mb:.1f}MB). "
            f"Consider reducing preloaded data. Render free tier limit is 512MB."
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown — release resources."""
    from backend.utils.memory import force_gc, log_memory
    force_gc()
    log_memory("shutdown")
    logger.info("Application shutdown complete.")


@app.get("/health")
async def health_check():
    """Health check with memory info for Render monitoring."""
    from backend.utils.memory import get_memory_usage_current_mb, get_memory_usage_mb
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "memory_mb": round(get_memory_usage_current_mb(), 1),
        "memory_peak_mb": round(get_memory_usage_mb(), 1),
    }


@app.get("/memory-status")
async def memory_status():
    """Detailed memory status endpoint for debugging on Render."""
    from backend.utils.memory import get_memory_usage_current_mb, get_memory_usage_mb
    import psutil
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return {
        "rss_mb": round(mem_info.rss / (1024 * 1024), 1),
        "vms_mb": round(mem_info.vms / (1024 * 1024), 1),
        "current_mb": round(get_memory_usage_current_mb(), 1),
        "peak_mb": round(get_memory_usage_mb(), 1),
        "render_limit_mb": 512,
        "headroom_mb": round(512 - get_memory_usage_current_mb(), 1),
    }


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
    from backend.utils.validators import get_processed_genes
    return list(get_processed_genes())
