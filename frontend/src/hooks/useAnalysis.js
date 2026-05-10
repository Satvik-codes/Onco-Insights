import { useContext } from 'react';
import { AnalysisContext } from '../state/analysisContext';
import { runFullAnalysis } from '../services/analysisService';

export const useAnalysis = () => {
  const { state, dispatch } = useContext(AnalysisContext);

  const runAnalysis = async (gene, cancer) => {
    dispatch({ type: 'ANALYSIS_START', payload: { query: { gene, cancer } } });

    const result = await runFullAnalysis(gene, cancer);

    if (result.success) {
      if (result.data.status === 'success') {
        dispatch({ type: 'ANALYSIS_SUCCESS', payload: result.data });
      } else if (result.data.status === 'partial') {
        dispatch({ type: 'ANALYSIS_PARTIAL', payload: result.data });
      } else {
        // top-level error in response
        dispatch({ type: 'ANALYSIS_ERROR', payload: { error: { message: "Analysis failed", ...result.data } } });
      }
    } else {
      dispatch({ type: 'ANALYSIS_ERROR', payload: { error: result.error } });
    }
  };

  const resetAnalysis = () => {
    dispatch({ type: 'RESET' });
  };

  return {
    status: state.status,
    results: state.results,
    query: state.query,
    globalError: state.globalError,
    reportUrl: state.reportUrl,
    runAnalysis,
    resetAnalysis
  };
};
