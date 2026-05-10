import pytest
from backend.analysis.expression_analysis import run_expression_analysis
import numpy as np

def test_expression_analysis_known_gene():
    result = run_expression_analysis("TP53", "BRCA")
    
    assert result["gene"] == "TP53"
    assert result["cancer"] == "BRCA"
    assert "tumor_count" in result
    assert "normal_count" in result
    assert result["fold_change"] > 0
    assert result["plot_json"] is not None
    assert result["direction"] in ["upregulated", "downregulated", "unchanged"]

def test_expression_analysis_unknown_gene():
    with pytest.raises(ValueError):
        run_expression_analysis("UNKNOWN_GENE", "BRCA")
