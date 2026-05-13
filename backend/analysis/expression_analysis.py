"""
Expression analysis — memory-optimized.

Changes from original:
- Uses load_expression_series() to read only the single gene row as a numpy array
- Downcasts float64 → float32
- No full DataFrame kept in memory
- Explicit cleanup of intermediate arrays
- Memory-aware logging
"""
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go
import json

from backend.config import SIGNIFICANCE_THRESHOLD
from backend.utils.logger import StructuredLogger
from backend.utils.data_loader import load_expression_series, cleanup_arrays
from backend.utils.memory import log_memory, downcast_numeric

logger = StructuredLogger(__name__)


def compute_tpm(log2_val: float) -> float:
    return max(0.0, (2 ** log2_val) - 0.001)


def run_expression_analysis(gene: str, cancer: str) -> dict:
    """
    Computes differential expression of a single gene between tumor and normal tissue.
    Memory-optimized: loads only the single gene row as numpy arrays.
    """
    logger.info(f"Starting expression analysis", metadata={"gene": gene, "cancer": cancer})
    log_memory(f"expr_start_{gene}_{cancer}")

    # Step 1 & 2: Load only the single gene's expression vectors
    tumor_expr = load_expression_series(cancer, gene, kind="tumor")
    normal_expr = load_expression_series(cancer, gene, kind="normal")

    if tumor_expr is None or len(tumor_expr) == 0:
        raise ValueError(f"Gene '{gene}' not found in tumor expression data for {cancer}")
    if normal_expr is None or len(normal_expr) == 0:
        raise ValueError(f"Gene '{gene}' not found in normal expression data for {cancer}")

    log_memory(f"expr_loaded_{gene}_{cancer}")

    tumor_count = len(tumor_expr)
    normal_count = len(normal_expr)

    # Step 3: Compute descriptive statistics (on float32 arrays)
    tumor_mean = float(np.mean(tumor_expr))
    normal_mean = float(np.mean(normal_expr))

    # Step 4: Compute fold change (in TPM space)
    # Vectorized TPM computation
    tumor_tpm = (2 ** tumor_expr) - 0.001
    tumor_tpm = np.maximum(tumor_tpm, 0.0)
    normal_tpm = (2 ** normal_expr) - 0.001
    normal_tpm = np.maximum(normal_tpm, 0.0)

    tumor_tpm_mean = float(np.mean(tumor_tpm))
    normal_tpm_mean = float(np.mean(normal_tpm))

    # Free intermediate TPM arrays
    del tumor_tpm, normal_tpm

    if normal_tpm_mean <= 0:
        fold_change = float('inf')
        log2_fc = 10.0
    else:
        fold_change = tumor_tpm_mean / normal_tpm_mean
        log2_fc = float(np.log2(fold_change)) if fold_change > 0 else -10.0

    # Step 5: Statistical testing
    # Subsample for Shapiro-Wilk if necessary
    max_sw = 5000
    if tumor_count > max_sw:
        tumor_sample_sw = np.random.choice(tumor_expr, max_sw, replace=False)
    else:
        tumor_sample_sw = tumor_expr

    if normal_count > max_sw:
        normal_sample_sw = np.random.choice(normal_expr, max_sw, replace=False)
    else:
        normal_sample_sw = normal_expr

    try:
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
    # Subsample for scatter points to avoid overcrowding
    max_points = 200
    if tumor_count <= max_points:
        tumor_points = tumor_expr
    else:
        tumor_points = np.random.choice(tumor_expr, max_points, replace=False)

    if normal_count <= max_points:
        normal_points = normal_expr
    else:
        normal_points = np.random.choice(normal_expr, max_points, replace=False)

    tumor_name = f"Tumor (N={tumor_count})"
    normal_name = f"Normal (N={normal_count})"

    fig = go.Figure()

    # Add Violin + Jitter for Normal
    fig.add_trace(go.Violin(
        y=normal_expr,
        name=normal_name,
        box_visible=True,
        meanline_visible=True,
        points=False,
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

    # Free arrays before building result
    cleanup_arrays(tumor_expr, normal_expr, tumor_points, normal_points)

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

    log_memory(f"expr_complete_{gene}_{cancer}")
    logger.info(f"Expression analysis completed for {gene}", metadata={"significant": result["significant"], "direction": result["direction"]})
    return result
