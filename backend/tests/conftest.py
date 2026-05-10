import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def mock_config_paths(monkeypatch):
    fixture_dir = Path(__file__).parent / "fixtures"
    
    import backend.analysis.expression_analysis as ea
    import backend.analysis.survival_analysis as sa
    import backend.analysis.mutation_analysis as ma
    
    monkeypatch.setattr(ea, "PROCESSED_EXPRESSION_DIR", fixture_dir / "processed" / "expression")
    
    monkeypatch.setattr(sa, "PROCESSED_EXPRESSION_DIR", fixture_dir / "processed" / "expression")
    monkeypatch.setattr(sa, "PROCESSED_CLINICAL_DIR", fixture_dir / "processed" / "clinical")
    
    monkeypatch.setattr(ma, "PROCESSED_MUTATION_DIR", fixture_dir / "processed" / "mutation")
    
    # We will also inject a mock index
    with open(fixture_dir / "processed" / "expression" / "gene_index.txt", "w") as f:
        for i in range(1, 51):
            f.write(f"GENE{i}\n")
        f.write("TP53\n")
        for i in range(1, 51):
            f.write(f"GENE{i}\n")
        f.write("TP53\n")
