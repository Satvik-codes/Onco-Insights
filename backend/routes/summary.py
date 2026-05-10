from fastapi import APIRouter, BackgroundTasks
from backend.models import AnalysisRequest, FullAnalysisResponse, ErrorDetail, SectionResult
from backend.routes.expression import analyze_expression
from backend.routes.survival import analyze_survival
from backend.routes.mutation import analyze_mutation
from backend.analysis.ai_summary import generate_ai_summary
from backend.utils.validators import validate_analysis_request
from backend.utils.cache_manager import cache
from backend.utils.logger import StructuredLogger
from backend.utils.report_generator import generate_pdf_report
import asyncio
from datetime import datetime
import httpx

logger = StructuredLogger(__name__)
router = APIRouter()

@router.post("/analyze", response_model=FullAnalysisResponse)
async def analyze_full(request: AnalysisRequest, background_tasks: BackgroundTasks):
    valid, gene, cancer, errors = validate_analysis_request(request.gene, request.cancer)
    if not valid:
        return {
            "status": "error",
            "gene": request.gene,
            "cancer": request.cancer,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "expression": {"status": "error", "error": {"error": True, "error_code": "VALIDATION_ERROR", "message": "Invalid request", "details": errors}},
            "survival": {"status": "error", "error": {"error": True, "error_code": "VALIDATION_ERROR", "message": "Invalid request", "details": errors}},
            "mutation": {"status": "error", "error": {"error": True, "error_code": "VALIDATION_ERROR", "message": "Invalid request", "details": errors}},
            "interpretation": {"status": "error", "error": {"error": True, "error_code": "VALIDATION_ERROR", "message": "Invalid request", "details": errors}},
        }
        
    cached = cache.get("full", gene, cancer)
    if cached:
        return cached

    # Run in parallel
    exp_task = analyze_expression(request)
    surv_task = analyze_survival(request)
    mut_task = analyze_mutation(request)
    
    exp_res, surv_res, mut_res = await asyncio.gather(exp_task, surv_task, mut_task)
    
    exp_success = exp_res.get("status") == "success"
    surv_success = surv_res.get("status") == "success"
    mut_success = mut_res.get("status") == "success"
    
    success_count = sum([exp_success, surv_success, mut_success])
    
    ai_res = {"status": "error", "error": {"error": True, "error_code": "AI_UNAVAILABLE", "message": "Not enough data for interpretation"}}
    
    if success_count >= 2:
        try:
            # We need the data payloads
            exp_data = exp_res.get("data", {})
            surv_data = surv_res.get("data", {})
            mut_data = mut_res.get("data", {})
            
            # Since HTTPClient is injected or global, ai_summary handles it.
            # wait, AI interpretation takes dicts. If one failed, we provide empty dict or handle it.
            ai_data = await generate_ai_summary(exp_data, surv_data, mut_data)
            ai_res = {"status": "success", "data": ai_data}
        except Exception as e:
            logger.error(f"AI Interpretation failed: {str(e)}", exc_info=True)
            ai_res = {"status": "error", "error": {"error": True, "error_code": "AI_UNAVAILABLE", "message": "AI interpretation failed"}}

    status = "success" if success_count == 3 else "partial"
    if success_count == 0:
        status = "error"
        
    response = {
        "status": status,
        "gene": gene,
        "cancer": cancer,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "expression": exp_res,
        "survival": surv_res,
        "mutation": mut_res,
        "interpretation": ai_res,
        "reportUrl": None
    }
    
    cache.set("full", gene, cancer, response)
    
    # Trigger PDF generation in background
    background_tasks.add_task(generate_pdf_report, response)
    
    return response
