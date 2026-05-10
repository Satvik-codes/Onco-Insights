from backend.utils.validators import validate_gene, validate_cancer, validate_analysis_request
import backend.utils.validators as validators

def test_validate_cancer():
    valid, code, err = validate_cancer("BRCA")
    assert valid is True
    assert code == "BRCA"
    
    valid, code, err = validate_cancer("breast invasive carcinoma")
    assert valid is True
    assert code == "BRCA"
    
    valid, code, err = validate_cancer("UNKNOWN")
    assert valid is False

def test_validate_gene(monkeypatch):
    # Mock HGNC and processed genes
    monkeypatch.setattr(validators, "HGNC_SYMBOLS", {"TP53", "EGFR"})
    monkeypatch.setattr(validators, "PROCESSED_GENES", {"TP53"})
    
    # Valid
    valid, norm, err = validate_gene("tp53")
    assert valid is True
    assert norm == "TP53"
    
    # Not in HGNC
    valid, norm, err = validate_gene("INVALID")
    assert valid is False
    assert "HGNC" in err
    
    # In HGNC but not processed
    valid, norm, err = validate_gene("EGFR")
    assert valid is False
    assert "processed" in err

def test_validate_analysis_request(monkeypatch):
    monkeypatch.setattr(validators, "HGNC_SYMBOLS", {"TP53"})
    monkeypatch.setattr(validators, "PROCESSED_GENES", {"TP53"})
    
    valid, gene, cancer, errors = validate_analysis_request("tp53", "brca")
    assert valid is True
    assert len(errors) == 0
    
    valid, gene, cancer, errors = validate_analysis_request("invalid", "unknown")
    assert valid is False
    assert len(errors) == 2
