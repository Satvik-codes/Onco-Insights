import httpx
import json
from typing import Dict, Any

from backend.config import (
    OPENROUTER_API_BASE_URL,
    OPENROUTER_API_KEY,
    AI_MODEL_NAME,
    AI_MAX_TOKENS,
    AI_TEMPERATURE
)
from backend.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)

# Global client for connection pooling
# In a real FastAPI app, this might be managed via lifespan events, but a global client works.
http_client = httpx.AsyncClient(timeout=30.0)

def generate_fallback_summary(expr_res: Dict[str, Any], surv_res: Dict[str, Any], mut_res: Dict[str, Any]) -> str:
    gene = expr_res['gene']
    cancer = expr_res['cancer']
    
    direction = expr_res.get('direction', 'unchanged')
    p_expr = expr_res.get('p_value', 1.0)
    hr = surv_res.get('hazard_ratio', 1.0)
    p_surv = surv_res.get('logrank_p_value', 1.0)
    mut_freq = mut_res.get('mutation_frequency_percent', 0.0)
    
    summary = (
        f"Analysis of {gene} in {cancer} indicates that expression is {direction} in tumor tissue (p={p_expr:.4f}). "
        f"Survival analysis shows a hazard ratio of {hr:.2f} (p={p_surv:.4f}) between high and low expression groups. "
        f"The gene is mutated in {mut_freq:.1f}% of the clinical cohort. "
        f"These statistical findings provide the baseline data for evaluating its potential as a biomarker."
    )
    return summary

async def generate_ai_summary(expr_res: Dict[str, Any], surv_res: Dict[str, Any], mut_res: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Starting AI summary generation")
    
    gene = expr_res.get('gene', 'Unknown')
    cancer = expr_res.get('cancer', 'Unknown')
    
    # Extract data for prompt
    prompt_data = {
        "gene": gene,
        "cancer": cancer,
        "expression": {
            "fold_change": expr_res.get("fold_change"),
            "log2_fold_change": expr_res.get("log2_fold_change"),
            "p_value": expr_res.get("p_value"),
            "direction": expr_res.get("direction"),
            "sample_counts": {"tumor": expr_res.get("tumor_count"), "normal": expr_res.get("normal_count")},
            "test_used": expr_res.get("statistical_test")
        },
        "survival": {
            "hazard_ratio": surv_res.get("hazard_ratio"),
            "hr_confidence_interval": surv_res.get("hr_confidence_interval"),
            "p_value": surv_res.get("logrank_p_value"),
            "median_survival_high_days": surv_res.get("median_survival_high"),
            "median_survival_low_days": surv_res.get("median_survival_low"),
            "significant": surv_res.get("significant")
        },
        "mutation": {
            "mutation_frequency_percent": mut_res.get("mutation_frequency_percent"),
            "cohort_size": mut_res.get("cohort_size")
        }
    }
    
    prompt = f"""
You are a bioinformatics assistant analyzing clinical genomic data.
Based ONLY on the following statistical results, write a concise, scientifically grounded interpretation.

Data:
{json.dumps(prompt_data, indent=2)}

Instructions:
1. Write 3-5 sentences maximum.
2. Use only the provided statistics - do not reference external knowledge or databases.
3. State whether the gene shows evidence of being a potential prognostic biomarker based solely on the provided data.
4. Use hedged scientific language ("suggests", "is associated with", "may indicate") rather than definitive causal claims.
5. Never mention specific drugs, therapies, or treatment recommendations.
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": AI_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": AI_TEMPERATURE,
        "max_tokens": AI_MAX_TOKENS
    }
    
    summary_text = ""
    generated_by = "ai"
    model_used = AI_MODEL_NAME
    
    try:
        # Retry logic: one retry
        for attempt in range(2):
            try:
                response = await http_client.post(
                    f"{OPENROUTER_API_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                summary_text = data['choices'][0]['message']['content'].strip()
                break
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == 1:
                    raise e
                logger.warning("OpenRouter API call failed, retrying...")
                
    except Exception as e:
        logger.error("AI summary generation failed, using fallback", exc_info=True)
        summary_text = generate_fallback_summary(expr_res, surv_res, mut_res)
        generated_by = "fallback_template"
        model_used = "template"
        
    result = {
        "summary": str(summary_text),
        "generated_by": str(generated_by),
        "model_used": str(model_used)
    }
    
    logger.info("AI summary generation completed", metadata={"generated_by": generated_by})
    return result
