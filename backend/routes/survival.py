from fastapi import APIRouter
from backend.models import AnalysisRequest, ErrorDetail
from backend.analysis.survival_analysis import run_survival_analysis
from backend.utils.validators import validate_analysis_request
from backend.utils.cache_manager import cache
from backend.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter()


@router.post("/survival")
async def analyze_survival(request: AnalysisRequest):
    valid, gene, cancer, errors = validate_analysis_request(request.gene, request.cancer)
    if not valid:
        return {"status": "error", "error": {"error": True, "error_code": "VALIDATION_ERROR", "message": "Invalid request", "details": errors}}

    cached = cache.get("survival", gene, cancer)
    if cached:
        return {"status": "success", "data": cached}

    try:
        result = run_survival_analysis(gene, cancer)
        cache.set("survival", gene, cancer, result)
        return {"status": "success", "data": result}
    except ValueError as e:
        err = ErrorDetail(error_code="INSUFFICIENT_SAMPLES", message=str(e))
        return {"status": "error", "error": err.model_dump()}
    except Exception as e:
        logger.error(f"Survival analysis failed: {str(e)}", exc_info=True)
        err = ErrorDetail(error_code="STATISTICAL_FAILURE", message="Survival analysis failed due to an internal error.")
        return {"status": "error", "error": err.model_dump()}
