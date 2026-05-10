import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from pathlib import Path
from typing import Dict, Any

from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test

from backend.config import (
    PROCESSED_EXPRESSION_DIR, 
    PROCESSED_CLINICAL_DIR, 
    SIGNIFICANCE_THRESHOLD,
    MIN_SURVIVAL_GROUP_SIZE,
    DEFAULT_SPLIT_STRATEGY
)
from backend.utils.logger import StructuredLogger
from backend.utils.id_normalizer import normalize_tcga_id

logger = StructuredLogger(__name__)

def run_survival_analysis(gene: str, cancer: str, split_strategy: str = DEFAULT_SPLIT_STRATEGY) -> Dict[str, Any]:
    logger.info("Starting survival analysis", metadata={"gene": gene, "cancer": cancer, "strategy": split_strategy})
    
    # Step 1: Load expression data
    tumor_expr_path = PROCESSED_EXPRESSION_DIR / f"{cancer.lower()}_tumor.parquet"
    try:
        expr_df = pd.read_parquet(tumor_expr_path)
        if gene not in expr_df.index:
            raise ValueError(f"Gene '{gene}' not found in expression data for {cancer}")
        gene_expr = expr_df.loc[gene]
    except Exception as e:
        logger.error("Failed to load expression data", exc_info=True)
        raise ValueError(f"Could not load expression data for {gene}")
        
    # Convert expression series to DataFrame and normalize IDs
    expr_data = pd.DataFrame({'expression': gene_expr}).reset_index()
    expr_data.columns = ['sample_id', 'expression']
    expr_data['normalized_id'] = expr_data['sample_id'].apply(normalize_tcga_id)
    expr_data = expr_data.dropna(subset=['normalized_id'])
    
    # Take mean expression if there are multiple samples per patient
    expr_data = expr_data.groupby('normalized_id', as_index=False)['expression'].mean()
    
    # Step 2: Load clinical data
    clinical_path = PROCESSED_CLINICAL_DIR / f"{cancer.lower()}_survival.parquet"
    try:
        clinical_df = pd.read_parquet(clinical_path)
    except Exception as e:
        logger.error("Failed to load clinical data", exc_info=True)
        raise ValueError(f"Could not load clinical survival data for {cancer}")
        
    # Step 3: Merge
    merged_df = pd.merge(expr_data, clinical_df, on='normalized_id', how='inner')
    
    if len(merged_df) == 0:
        logger.error("Merged expression and clinical data resulted in 0 samples")
        raise ValueError("Failed to merge expression and clinical data (0 matching patients).")
        
    logger.info(f"Merged survival data: {len(merged_df)} patients available")
    
    # Step 4: Split patients
    if split_strategy == "median":
        split_value = merged_df['expression'].median()
    else:
        # Architecturally ready for quartile/percentile but default to median
        split_value = merged_df['expression'].median()
        split_strategy = "median"
        
    merged_df['group'] = np.where(merged_df['expression'] > split_value, 'High', 'Low')
    
    # Remove exact median from both to be strict if desired, but standard is > vs <=
    # The blueprint says: "Patients above the median are 'High', at or below are 'Low'."
    merged_df['group'] = np.where(merged_df['expression'] > split_value, 'High', 'Low')
    
    high_group = merged_df[merged_df['group'] == 'High']
    low_group = merged_df[merged_df['group'] == 'Low']
    
    high_count = len(high_group)
    low_count = len(low_group)
    
    # Step 5: Validate sizes
    if high_count < MIN_SURVIVAL_GROUP_SIZE or low_count < MIN_SURVIVAL_GROUP_SIZE:
        logger.error(f"Insufficient group sizes: High={high_count}, Low={low_count}")
        raise ValueError(f"Insufficient patient samples for survival analysis (High: {high_count}, Low: {low_count}). Minimum required is {MIN_SURVIVAL_GROUP_SIZE} per group.")
        
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
    
    cph = CoxPHFitter()
    try:
        cph.fit(cox_df, duration_col='survival_time', event_col='survival_event')
        hr = cph.hazard_ratios_['High_Expr']
        ci_lower = cph.confidence_intervals_.iloc[0, 0]
        ci_upper = cph.confidence_intervals_.iloc[0, 1]
        
        hr_val = float(hr)
        hr_ci = [float(np.exp(ci_lower)), float(np.exp(ci_upper))]
    except Exception as e:
        logger.warning("CoxPHFitter failed to converge, returning defaults", exc_info=True)
        hr_val = 1.0
        hr_ci = [1.0, 1.0]
        
    is_significant = bool(p_value <= SIGNIFICANCE_THRESHOLD)
    
    # Step 9: Visualization
    fig = go.Figure()
    
    # Plotly KM curves
    for kmf, name, color in [(kmf_high, f"High Expression (N={high_count})", "#e34a33"), 
                             (kmf_low, f"Low Expression (N={low_count})", "#2b8cbe")]:
        
        # Survival function
        surv = kmf.survival_function_
        ci = kmf.confidence_interval_
        
        times = surv.index.values
        probs = surv[kmf.survival_function_.columns[0]].values
        
        ci_lower = ci[ci.columns[0]].values
        ci_upper = ci[ci.columns[1]].values
        
        # Add Confidence Intervals
        fig.add_trace(go.Scatter(
            x=list(times) + list(times)[::-1],
            y=list(ci_upper) + list(ci_lower)[::-1],
            fill='toself',
            fillcolor=color,
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=False,
            opacity=0.2
        ))
        
        # Add survival line (step shape)
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
    
    logger.info("Survival analysis completed successfully")
    return result
