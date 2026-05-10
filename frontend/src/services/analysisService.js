import api from './api';

export const runFullAnalysis = async (gene, cancer) => {
  try {
    const response = await api.post('/analyze', { gene, cancer });
    return { success: true, data: response.data, error: null };
  } catch (error) {
    return { success: false, data: null, error };
  }
};

export const runExpressionAnalysis = async (gene, cancer) => {
  try {
    const response = await api.post('/expression', { gene, cancer });
    return { success: true, data: response.data, error: null };
  } catch (error) {
    return { success: false, data: null, error };
  }
};

export const runSurvivalAnalysis = async (gene, cancer) => {
  try {
    const response = await api.post('/survival', { gene, cancer });
    return { success: true, data: response.data, error: null };
  } catch (error) {
    return { success: false, data: null, error };
  }
};

export const runMutationAnalysis = async (gene, cancer) => {
  try {
    const response = await api.post('/mutation', { gene, cancer });
    return { success: true, data: response.data, error: null };
  } catch (error) {
    return { success: false, data: null, error };
  }
};
