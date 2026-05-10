import React, { useState, useEffect } from 'react';
import { useGeneAutocomplete } from '../../hooks/useGeneAutocomplete';
import { validateGene } from '../../services/geneService';

const GeneSearchBar = ({ value, onChange, cancerType, onValidation }) => {
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  
  const { geneList, loading } = useGeneAutocomplete();

  const runValidation = async (gene, cancer) => {
    if (!gene || !cancer) {
      setValidationResult(null);
      if (onValidation) onValidation(false);
      return;
    }
    
    setIsValidating(true);
    const result = await validateGene(gene, cancer);
    setValidationResult(result);
    setIsValidating(false);
    
    if (onValidation) onValidation(result.valid);
  };

  const handleInputChange = (e) => {
    const gene = e.target.value.toUpperCase();
    onChange(gene);
    setValidationResult(null);
    if (onValidation) onValidation(false);
  };

  const handleBlur = async (e) => {
    const gene = e.target.value.toUpperCase();
    if (gene) {
      await runValidation(gene, cancerType);
    }
  };

  // Re-validate when cancer type changes
  useEffect(() => {
    if (value && cancerType) {
      runValidation(value, cancerType);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cancerType]);

  return (
    <div className="gene-search-bar">
      <div className="input-wrapper">
        <input 
          type="text"
          className="gene-input monospace" 
          placeholder={loading ? "Loading genes..." : "Enter or select a gene symbol (e.g. TP53)"}
          value={value || ''}
          onChange={handleInputChange}
          onBlur={handleBlur}
          list="gene-options"
          autoComplete="off"
          style={{ width: '100%', backgroundColor: '#1e2128', color: '#e0e6ed', border: '1px solid #2d3748', padding: '10px 15px', borderRadius: '4px' }}
        />
        <datalist id="gene-options">
          {geneList.map((gene, idx) => (
            <option key={idx} value={gene} />
          ))}
        </datalist>
        <div className="validation-indicator" style={{ position: 'absolute', right: '35px', top: '50%', transform: 'translateY(-50%)' }}>
          {isValidating && <span className="spinner-small">...</span>}
          {!isValidating && validationResult && validationResult.valid && <span className="valid-mark">✓</span>}
          {!isValidating && validationResult && !validationResult.valid && <span className="invalid-mark" title={validationResult.error_message}>✗</span>}
        </div>
      </div>
      
      {validationResult && !validationResult.valid && (
        <div className="validation-error-message text-error">
          {validationResult.error_message}
        </div>
      )}
    </div>
  );
};

export default GeneSearchBar;
