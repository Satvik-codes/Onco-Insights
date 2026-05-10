import { useState, useEffect, useCallback } from 'react';
import { fetchGeneList } from '../services/geneService';

export const useGeneAutocomplete = () => {
  const [geneList, setGeneList] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    
    const loadGenes = async () => {
      setLoading(true);
      const genes = await fetchGeneList();
      if (mounted) {
        setGeneList(genes);
        setLoading(false);
      }
    };
    
    loadGenes();
    
    return () => { mounted = false; };
  }, []);

  const filterSuggestions = useCallback((input) => {
    if (!input || input.trim() === '') {
      setSuggestions([]);
      return;
    }
    
    const upperInput = input.trim().toUpperCase();
    
    // exact prefix matching
    const matches = geneList
      .filter(gene => gene.toUpperCase().startsWith(upperInput))
      .slice(0, 10); // limit to top 10
      
    setSuggestions(matches);
  }, [geneList]);

  return { geneList, suggestions, loading, filterSuggestions };
};
