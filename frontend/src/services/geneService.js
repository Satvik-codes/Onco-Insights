import api from './api';

let cachedGenes = null;

export const fetchGeneList = async () => {
  if (cachedGenes) {
    return cachedGenes;
  }
  
  try {
    const response = await api.get('/genes');
    cachedGenes = response.data;
    return cachedGenes;
  } catch (error) {
    console.error('Failed to fetch gene list:', error);
    return [];
  }
};

export const validateGene = async (gene, cancer) => {
  try {
    const response = await api.get(`/validate?gene=${encodeURIComponent(gene)}&cancer=${encodeURIComponent(cancer)}`);
    return response.data;
  } catch (error) {
    // API errors are normalized by the interceptor
    return { valid: false, error_message: error.message };
  }
};
