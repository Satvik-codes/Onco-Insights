import pytest
from backend.analysis.mutation_analysis import run_mutation_analysis

def test_mutation_analysis_with_mutations():
    result = run_mutation_analysis("TP53", "BRCA")
    
    assert result["gene"] == "TP53"
    assert result["cohort_size"] == 30
    assert result["mutated_patients"] > 0
    assert result["mutation_frequency_percent"] > 0
    assert result["has_mutations"] is True
    assert "Missense" in result["mutation_types"]
    assert "frequency_plot_json" in result
    assert "type_plot_json" in result

def test_mutation_analysis_no_mutations():
    # GENE1 shouldn't have mutations in our fixture if we only gave mutations to randomly selected and TP53
    # Wait, our random selection might have included GENE1. Let's test a gene definitely not in mut fixture.
    result = run_mutation_analysis("UNKNOWN_GENE", "BRCA")
    
    assert result["mutated_patients"] == 0
    assert result["mutation_frequency_percent"] == 0.0
    assert result["has_mutations"] is False
    assert sum(result["mutation_types"].values()) == 0
