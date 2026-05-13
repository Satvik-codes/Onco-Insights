"""
Survival analysis — memory-optimized.

Changes from original:
- Uses load_survival_inputs() which reads expression as a numpy array (not full DataFrame)
- Uses load_clinical() for on-demand clinical data loading
- Avoids unnecessary DataFrame copies
- Downcasts numeric types
- Explicit cleanup of intermediate DataFrames
- Memory-aware logging
"""
import numpy as np
import pandas as pd
import json
import plotly.graph_objects as go

from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test

from backend.config import SIGNIFICANCE_THRESHOLD, MIN_SURVIVAL_GROUP_SIZE, DEFAULT_SPLIT_STRATEGY
from backend.utils.logger import StructuredLogger
from backend.utils.id_normalizer import normalize_tcga_id
from backend.utils.data_loader import load_survival_inputs, cleanup_dataframe, cleanup_arrays, downcast_numeric
from backend.utils.memory import log_memory, force_gc

logger = StructuredLogger(__name__)


def run_survival_analysis(gene: str, cancer: str, split_strategy: str = DEFAULT_SPLIT_STRATEGY) -> dict:
    """
    Runs survival analysis with memory-efficient data loading.
    Only loads data for the requested cancer type and gene.
    """
    logger.info("Starting survival analysis", metadata={"gene": gene, "cancer": cancer, "strategy": split_strategy})
    log_memory(f"surv_start_{gene}_{cancer}")

    # Step 1: Load expression as numpy array + sample IDs + clinical data
    expr_arr, sample_ids, clinical_df = load_survival_inputs(cancer, gene)

    if expr_arr is None or len(expr_arr) == 0:
        cleanup_dataframe(clinical_df)
        raise ValueError(f"Gene '{gene}' not found in expression data for {cancer}")

    log_memory(f"surv_data_loaded_{gene}_{cancer}")

    # Step 2: Build expression DataFrame for merging with clinical
    # Create a DataFrame from the numpy array and sample IDs
    expr_df = pd.DataFrame({
        'sample_id': sample_ids,
        'expression': expr_arr
    })
    del sample_ids, expr_arr
    force_gc()

    # Normalize sample IDs
    expr_df['normalized_id'] = expr_df['sample_id'].apply(normalize_tcga_id)
    expr_df = expr_df.dropna(subset=['normalized_id'])

    # Take mean expression if there are multiple samples per patient
    expr_for_merge = expr_df.groupby('normalized_id', as_index=False)['expression'].mean()
    del expr_df
    force_gc()

    downcast_numeric(expr_for_merge)
    log_memory(f"surv_expr_prep_{gene}_{cancer}")

    # Step 3: Merge expression with clinical
    merged_df = pd.merge(expr_for_merge, clinical_df, on='normalized_id', how='inner')
    del expr_for_merge, clinical_df
    force_gc()

    if len(merged_df) == 0:
        raise ValueError("Failed to merge expression and clinical data (0 matching patients).")

    logger.info(f"Merged survival data: {len(merged_df)} patients available")
    log_memory(f"surv_merged_{gene}_{cancer}")

    # Step 4: Split patients
    if split_strategy == "median":
        split_value = merged_df['expression'].median()
    else:
        split_value = merged_df['expression'].median()
        split_strategy = "median"

    merged_df['group'] = np.where(merged_df['expression'] > split_value, 'High', 'Low')

    high_group = merged_df[merged_df['group'] == 'High']
    low_group = merged_df[merged_df['group'] == 'Low']

    high_count = len(high_group)
    low_count = len(low_group)

    # Step 5: Validate sizes
    if high_count < MIN_SURVIVAL_GROUP_SIZE or low_count < MIN_SURVIVAL_GROUP_SIZE:
        raise ValueError(
            f"Insufficient patient samples for survival analysis (High: {high_count}, Low: {low_count}). "
            f"Minimum required is {MIN_SURVIVAL_GROUP_SIZE} per group."
        )

    # Step 6: Kaplan-Meier Estimation
    kmf_high = KaplanMeierFitter()
    kmf_low = KaplanMeierFitter()

    kmf_high.fit(high_group['survival_time'], event_observed=high_group['survival_event'], label='High Expression')
    kmf_low.fit(low_group['survival_time'], event_observed=low_group['survival_event'], label='Low Expression')

    median_high = kmf_high.median_survival_time_
    median_low = kmf_low.median_survival_time_

    median_high_val = float(median_high) if not np.isinf(median_high) else -1.0
    median_low_val = float(median_low) if not np.isinf(median_low) else -1.0

    # Step 7: Log-rank test
    results = logrank_test(
        high_group['survival_time'], low_group['survival_time'],
        event_observed_A=high_group['survival_event'], event_observed_B=low_group['survival_event']
    )
    p_value = float(results.p_value)

    # Step 8: Hazard Ratio
    cox_df = merged_df[['survival_time', 'survival_event', 'group']].copy()
    cox_df['High_Expr'] = (cox_df['group'] == 'High').astype(int)
    cox_df = cox_df[['survival_time', 'survival_event', 'High_Expr']]

    try:
        cph = CoxPHFitter()
        cph.fit(cox_df, duration_col='survival_time', event_col='survival_event')
        hr = cph.hazard_ratios_['High_Expr']
        ci_lower = cph.confidence_intervals_.iloc[0, 0]
        ci_upper = cph.confidence_intervals_.iloc[0, 1]

        hr_val = float(hr)
        hr_ci = [float(np.exp(ci_lower)), float(np.exp(ci_upper))]
    except Exception:
        hr_val = 1.0
        hr_ci = [1.0, 1.0]

    is_significant = bool(p_value <= SIGNIFICANCE_THRESHOLD)

    # Step 9: Visualization
    fig = go.Figure()

    for kmf, name, color in [
        (kmf_high, f"High Expression (N={high_count})", "#e34a33"),
        (kmf_low, f"Low Expression (N={low_count})", "#2b8cbe")
    ]:
        surv = kmf.survival_function_
        ci = kmf.confidence_interval_

        times = surv.index.values
        probs = surv[kmf.survival_function_.columns[0]].values

        ci_lower_vals = ci[ci.columns[0]].values
        ci_upper_vals = ci[ci.columns[1]].values

        # Confidence interval band
        fig.add_trace(go.Scatter(
            x=list(times) + list(times)[::-1],
            y=list(ci_upper_vals) + list(ci_lower_vals)[::-1],
            fill='toself',
            fillcolor=color,
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=False,
            opacity=0.2
        ))

        # Survival line
        fig.add_trace(go.Scatter(
            x=times,
            y=probs,
            mode='lines',
            line=dict(shape='hv', color=color, width=2),
            name=name
        ))

    p_formatted = f"p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"
    hr_formatted = f"HR = {hr_val:.2f} ({hr_ci[0]:.2f}-{hr_ci[1]:.2f})"

    fig.update_layout(
        title=f"{gene} Survival Analysis in {cancer}<br><sup>Log-rank {p_formatted} | {hr_formatted}</sup>",
        xaxis_title="Overall Survival Time (Days)",
        yaxis_title="Survival Probability",
        yaxis=dict(range=[0, 1.05]),
        legend=dict(x=0.7, y=0.9),
        template="simple_white"
    )

    plot_json = json.loads(fig.to_json())

    # Cleanup
    cleanup_dataframe(merged_df)
    cleanup_dataframe(high_group)
    cleanup_dataframe(low_group)
    cleanup_dataframe(cox_df)

    result = {
        "gene": str(gene),
        "cancer": str(cancer),
        "high_count": int(high_count),
        "low_count": int(low_count),
        "median_survival_high": float(median_high_val),
        "median_survival_low": float(median_low_val),
        "logrank_p_value": float(p_value),
        "hazard_ratio": float(hr_val),
        "hr_confidence_interval": [float(hr_ci[0]), float(hr_ci[1])],
        "significant": bool(is_significant),
        "split_strategy": str(split_strategy),
        "split_value": float(split_value),
        "plot_json": plot_json
    }

    log_memory(f"surv_complete_{gene}_{cancer}")
    logger.info("Survival analysis completed successfully")
    return result
