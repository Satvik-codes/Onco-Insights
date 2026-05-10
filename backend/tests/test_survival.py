import pytest
from backend.analysis.survival_analysis import run_survival_analysis
from backend.config import MIN_SURVIVAL_GROUP_SIZE

# For testing, we might need to lower MIN_SURVIVAL_GROUP_SIZE because our fixture only has 30 patients (15 per group)
@pytest.fixture(autouse=True)
def override_group_size(monkeypatch):
    import backend.analysis.survival_analysis as sa
    monkeypatch.setattr(sa, "MIN_SURVIVAL_GROUP_SIZE", 10)

def test_survival_analysis_median_split():
    result = run_survival_analysis("TP53", "BRCA", "median")
    
    assert result["gene"] == "TP53"
    assert result["high_count"] > 0
    assert result["low_count"] > 0
    assert "hazard_ratio" in result
    assert "logrank_p_value" in result
    assert "hr_confidence_interval" in result
    assert len(result["hr_confidence_interval"]) == 2
    assert result["plot_json"] is not None

def test_survival_analysis_insufficient_samples(monkeypatch):
    import backend.analysis.survival_analysis as sa
    monkeypatch.setattr(sa, "MIN_SURVIVAL_GROUP_SIZE", 100)
    with pytest.raises(ValueError, match="Insufficient patient samples"):
        run_survival_analysis("TP53", "BRCA", "median")
