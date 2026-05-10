import pandas as pd
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go
import json
from pathlib import Path
from typing import Dict, Any, Tuple

from backend.config import PROCESSED_EXPRESSION_DIR, SIGNIFICANCE_THRESHOLD
from backend.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)

def get_gene_expression(file_path: Path, gene: str) -> np.ndarray:
    """Reads expression vector for a single gene from a parquet file."""
    try:
        # Try reading just the specific row by index if possible
        # Some parquet engines support reading specific rows if index is preserved
        df = pd.read_parquet(file_path)
        if gene in df.index:
            return df.loc[gene].values.astype(float)
        else:
            return np.array([])
    except Exception as e:
        logger.error(f"Failed to load expression data from {file_path}", exc_info=True)
        return np.array([])

def compute_tpm(log2_val: float) -> float:
    return max(0.0, (2 ** log2_val) - 0.001)

def run_expression_analysis(gene: str, cancer: str) -> Dict[str, Any]:
    """
    Computes differential expression of a single gene between tumor and normal tissue.
    """
    logger.info(f"Starting expression analysis", metadata={"gene": gene, "cancer": cancer})
    
    tumor_path = PROCESSED_EXPRESSION_DIR / f"{cancer.lower()}_tumor.parquet"
    normal_path = PROCESSED_EXPRESSION_DIR / f"{cancer.lower()}_normal.parquet"
    
    # Step 1 & 2: Load data
    tumor_expr = get_gene_expression(tumor_path, gene)
    normal_expr = get_gene_expression(normal_path, gene)
    
    tumor_count = len(tumor_expr)
    normal_count = len(normal_expr)
    
    # Check for empty data
    if tumor_count == 0 or normal_count == 0:
        logger.error(f"Missing expression data for {gene} in {cancer}")
        raise ValueError(f"Gene '{gene}' not found in expression data for {cancer}")
        
    # Step 3: Compute descriptive statistics
    tumor_mean = float(np.mean(tumor_expr))
    normal_mean = float(np.mean(normal_expr))
    
    # Step 4: Compute fold change (in TPM space)
    tumor_tpm_mean = float(np.mean([compute_tpm(x) for x in tumor_expr]))
    normal_tpm_mean = float(np.mean([compute_tpm(x) for x in normal_expr]))
    
    if normal_tpm_mean <= 0:
        fold_change = float('inf')
        log2_fc = 10.0 # arbitrary high value
    else:
        fold_change = tumor_tpm_mean / normal_tpm_mean
        log2_fc = float(np.log2(fold_change)) if fold_change > 0 else -10.0
        
    # Step 5: Statistical testing
    # Subsample for Shapiro-Wilk if necessary
    tumor_sample_sw = tumor_expr if tumor_count <= 5000 else np.random.choice(tumor_expr, 5000, replace=False)
    normal_sample_sw = normal_expr if normal_count <= 5000 else np.random.choice(normal_expr, 5000, replace=False)
    
    try:
        # Avoid Shapiro-Wilk crashing if all values are identical
        if np.var(tumor_sample_sw) == 0 or np.var(normal_sample_sw) == 0:
            tumor_normal_p = 0.0
            normal_normal_p = 0.0
        else:
            _, tumor_normal_p = stats.shapiro(tumor_sample_sw)
            _, normal_normal_p = stats.shapiro(normal_sample_sw)
    except Exception:
        tumor_normal_p = 0.0
        normal_normal_p = 0.0
        
    alpha_normality = 0.05
    is_tumor_normal = tumor_normal_p > alpha_normality
    is_normal_normal = normal_normal_p > alpha_normality
    
    if is_tumor_normal and is_normal_normal:
        stat_test = "Welch's t-test"
        # Welch's t-test (equal_var=False)
        _, p_value = stats.ttest_ind(tumor_expr, normal_expr, equal_var=False)
    else:
        stat_test = "Mann-Whitney U test"
        _, p_value = stats.mannwhitneyu(tumor_expr, normal_expr, alternative='two-sided')
        
    p_value = float(p_value)
    if np.isnan(p_value):
        p_value = 1.0
        
    is_significant = bool(p_value <= SIGNIFICANCE_THRESHOLD)
    
    if is_significant and log2_fc > 1.0:
        direction = "upregulated"
    elif is_significant and log2_fc < -1.0:
        direction = "downregulated"
    else:
        direction = "unchanged"
        
    # Step 6: Generate Visualization
    fig = go.Figure()
    
    # Subsample for scatter points to avoid overcrowding
    max_points = 200
    tumor_points = tumor_expr if tumor_count <= max_points else np.random.choice(tumor_expr, max_points, replace=False)
    normal_points = normal_expr if normal_count <= max_points else np.random.choice(normal_expr, max_points, replace=False)
    
    tumor_name = f"Tumor (N={tumor_count})"
    normal_name = f"Normal (N={normal_count})"
    
    # Add Violin + Jitter for Normal
    fig.add_trace(go.Violin(
        y=normal_expr,
        name=normal_name,
        box_visible=True,
        meanline_visible=True,
        points=False, # We'll add custom scatter below
        line_color="#2b8cbe"
    ))
    
    fig.add_trace(go.Scatter(
        y=normal_points,
        x=np.random.normal(0, 0.04, size=len(normal_points)),
        mode='markers',
        marker=dict(color="#2b8cbe", size=4, opacity=0.5),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add Violin + Jitter for Tumor
    fig.add_trace(go.Violin(
        y=tumor_expr,
        name=tumor_name,
        box_visible=True,
        meanline_visible=True,
        points=False,
        line_color="#e34a33"
    ))
    
    fig.add_trace(go.Scatter(
        y=tumor_points,
        x=np.random.normal(1, 0.04, size=len(tumor_points)),
        mode='markers',
        marker=dict(color="#e34a33", size=4, opacity=0.5),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    p_formatted = f"p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"
    
    fig.update_layout(
        title=f"{gene} Expression in {cancer} Tumor vs Normal<br><sup>{stat_test}, {p_formatted}</sup>",
        yaxis_title="log2(TPM + 0.001)",
        xaxis_title="",
        showlegend=False,
        template="simple_white",
        violingap=0.3
    )
    
    plot_json = json.loads(fig.to_json())
    
    result = {
        "gene": str(gene),
        "cancer": str(cancer),
        "tumor_count": int(tumor_count),
        "normal_count": int(normal_count),
        "tumor_mean_log2": float(tumor_mean),
        "normal_mean_log2": float(normal_mean),
        "fold_change": float(fold_change),
        "log2_fold_change": float(log2_fc),
        "p_value": float(p_value),
        "statistical_test": str(stat_test),
        "significant": bool(is_significant),
        "direction": str(direction),
        "plot_json": plot_json
    }
    
    logger.info(f"Expression analysis completed for {gene}", metadata={"significant": result["significant"], "direction": result["direction"]})
    return result
