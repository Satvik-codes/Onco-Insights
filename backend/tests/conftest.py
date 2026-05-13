import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def mock_config_paths(monkeypatch):
    fixture_dir = Path(__file__).parent / "fixtures"

    import backend.utils.data_loader as dl
    import backend.utils.validators as val

    # Patch data_loader module (refactored code reads paths through here)
    monkeypatch.setattr(dl, "PROCESSED_EXPRESSION_DIR", fixture_dir / "processed" / "expression")
    monkeypatch.setattr(dl, "PROCESSED_CLINICAL_DIR", fixture_dir / "processed" / "clinical")
    monkeypatch.setattr(dl, "PROCESSED_MUTATION_DIR", fixture_dir / "processed" / "mutation")

    # Patch validators module (lazy-loads gene index from expression dir)
    monkeypatch.setattr(val, "PROCESSED_EXPRESSION_DIR", fixture_dir / "processed" / "expression")

    # Reset lazy-loaded caches so fixtures take effect
    dl._gene_index = None
    dl._cohort_sizes = None
    val._genes_loaded = False
    val._PROCESSED_GENES = set()

    # Write gene index with TP53 for tests
    gene_index_path = fixture_dir / "processed" / "expression" / "gene_index.txt"
    with open(gene_index_path, "w") as f:
        for i in range(1, 51):
            f.write(f"GENE{i}\n")
        f.write("TP53\n")
