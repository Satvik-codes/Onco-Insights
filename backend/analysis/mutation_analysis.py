import pandas as pd
import json
import plotly.graph_objects as go
from pathlib import Path
from typing import Dict, Any

from backend.config import PROCESSED_MUTATION_DIR
from backend.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)

def run_mutation_analysis(gene: str, cancer: str) -> Dict[str, Any]:
    logger.info("Starting mutation analysis", metadata={"gene": gene, "cancer": cancer})
    
    # Step 1: Load processed mutation data
    mutation_path = PROCESSED_MUTATION_DIR / f"{cancer.lower()}_mutations.parquet"
    cohort_sizes_path = PROCESSED_MUTATION_DIR / "cohort_sizes.json"
    
    try:
        with open(cohort_sizes_path, 'r', encoding='utf-8') as f:
            cohort_sizes = json.load(f)
            
        cohort_size = cohort_sizes.get(cancer)
        if not cohort_size:
            raise ValueError(f"Cohort size not found for {cancer}")
            
        df = pd.read_parquet(mutation_path)
    except Exception as e:
        logger.error("Failed to load mutation data", exc_info=True)
        raise ValueError(f"Could not load mutation data for {cancer}")
        
    # Step 2: Filter for queried gene
    gene_df = df[df['Hugo_Symbol'] == gene]
    
    # Step 3: Compute frequency
    if gene_df.empty:
        mutated_patients = 0
        mutation_frequency = 0.0
        has_mutations = False
    else:
        mutated_patients = int(gene_df['normalized_id'].nunique())
        mutation_frequency = float((mutated_patients / cohort_size) * 100)
        has_mutations = True
        
    # Step 4: Compute distribution
    types_dict = {
        "Missense": 0,
        "Nonsense": 0,
        "Frameshift": 0,
        "Splice Site": 0,
        "In-frame Indel": 0,
        "Silent": 0,
        "Other": 0
    }
    
    if has_mutations:
        type_counts = gene_df['mutation_type'].value_counts().to_dict()
        for t, count in type_counts.items():
            if t in types_dict:
                types_dict[t] = int(count)
            else:
                types_dict["Other"] += int(count)
                
    # Step 5: Visualizations
    
    # Fig 1: Frequency card
    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        x=[mutation_frequency],
        y=[gene],
        orientation='h',
        marker_color="#2b8cbe",
        text=f"{mutation_frequency:.1f}% of {cohort_size} patients",
        textposition='auto'
    ))
    
    fig1.update_layout(
        title=f"{gene} Mutation Frequency in {cancer}",
        xaxis=dict(title="Mutation Rate (%)", range=[0, max(10, mutation_frequency + 5)]),
        yaxis=dict(showticklabels=False),
        height=250,
        template="simple_white",
        margin=dict(l=20, r=20, t=50, b=40)
    )
    freq_plot_json = json.loads(fig1.to_json())
    
    # Fig 2: Type distribution
    fig2 = go.Figure()
    
    if has_mutations:
        labels = [k for k, v in types_dict.items() if v > 0]
        values = [v for k, v in types_dict.items() if v > 0]
        
        fig2.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo='label+percent'
        ))
    else:
        fig2.add_annotation(
            text="No mutations detected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig2.update_xaxes(visible=False)
        fig2.update_yaxes(visible=False)
        
    fig2.update_layout(
        title=f"{gene} Mutation Types in {cancer}",
        height=400,
        template="simple_white"
    )
    type_plot_json = json.loads(fig2.to_json())
    
    result = {
        "gene": str(gene),
        "cancer": str(cancer),
        "cohort_size": int(cohort_size),
        "mutated_patients": int(mutated_patients),
        "mutation_frequency_percent": float(mutation_frequency),
        "mutation_types": types_dict,
        "has_mutations": bool(has_mutations),
        "frequency_plot_json": freq_plot_json,
        "type_plot_json": type_plot_json
    }
    
    logger.info("Mutation analysis completed successfully")
    return result
