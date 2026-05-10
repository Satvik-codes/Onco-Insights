from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class AnalysisRequest(BaseModel):
    gene: str = Field(..., description="HGNC approved gene symbol")
    cancer: str = Field(..., description="TCGA cancer code (BRCA, LUAD, COAD)")

class ErrorDetail(BaseModel):
    error: bool = True
    error_code: str
    message: str
    details: Optional[Any] = None

class SectionResult(BaseModel):
    # This can hold the specific fields for each analysis or an error
    status: str # "success" or "error"
    data: Optional[Dict[str, Any]] = None
    error: Optional[ErrorDetail] = None

class FullAnalysisResponse(BaseModel):
    status: str # "success", "partial", "error"
    gene: str
    cancer: str
    timestamp: str
    expression: SectionResult
    survival: SectionResult
    mutation: SectionResult
    interpretation: SectionResult
    reportUrl: Optional[str] = None
