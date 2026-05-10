export const initialState = {
  query: { gene: '', cancer: '' },
  status: 'idle', // 'idle' | 'loading' | 'partial' | 'complete' | 'error'
  results: {
    expression: { status: 'idle', data: null, error: null },
    survival: { status: 'idle', data: null, error: null },
    mutation: { status: 'idle', data: null, error: null },
    interpretation: { status: 'idle', data: null, error: null }
  },
  reportUrl: null,
  lastAnalyzedAt: null,
  globalError: null
};

export function analysisReducer(state, action) {
  switch (action.type) {
    case 'ANALYSIS_START':
      return {
        ...state,
        query: action.payload.query,
        status: 'loading',
        globalError: null,
        results: {
          expression: { status: 'loading', data: null, error: null },
          survival: { status: 'loading', data: null, error: null },
          mutation: { status: 'loading', data: null, error: null },
          interpretation: { status: 'loading', data: null, error: null }
        },
        reportUrl: null,
        lastAnalyzedAt: null
      };

    case 'ANALYSIS_SUCCESS':
      return {
        ...state,
        status: 'complete',
        results: {
          expression: { status: 'success', data: action.payload.expression.data, error: null },
          survival: { status: 'success', data: action.payload.survival.data, error: null },
          mutation: { status: 'success', data: action.payload.mutation.data, error: null },
          interpretation: { status: 'success', data: action.payload.interpretation.data, error: null }
        },
        reportUrl: action.payload.reportUrl || null,
        lastAnalyzedAt: new Date().toISOString()
      };

    case 'ANALYSIS_PARTIAL':
      return {
        ...state,
        status: 'partial',
        results: {
          expression: action.payload.expression.error 
            ? { status: 'error', data: null, error: action.payload.expression.error }
            : { status: 'success', data: action.payload.expression.data, error: null },
          survival: action.payload.survival.error 
            ? { status: 'error', data: null, error: action.payload.survival.error }
            : { status: 'success', data: action.payload.survival.data, error: null },
          mutation: action.payload.mutation.error 
            ? { status: 'error', data: null, error: action.payload.mutation.error }
            : { status: 'success', data: action.payload.mutation.data, error: null },
          interpretation: action.payload.interpretation.error 
            ? { status: 'error', data: null, error: action.payload.interpretation.error }
            : { status: 'success', data: action.payload.interpretation.data, error: null }
        },
        reportUrl: action.payload.reportUrl || null,
        lastAnalyzedAt: new Date().toISOString()
      };

    case 'ANALYSIS_ERROR':
      return {
        ...state,
        status: 'error',
        globalError: action.payload.error,
        results: {
          expression: { status: 'error', data: null, error: action.payload.error },
          survival: { status: 'error', data: null, error: action.payload.error },
          mutation: { status: 'error', data: null, error: action.payload.error },
          interpretation: { status: 'error', data: null, error: action.payload.error }
        }
      };

    case 'SECTION_ERROR':
      return {
        ...state,
        results: {
          ...state.results,
          [action.payload.section]: { status: 'error', data: null, error: action.payload.error }
        }
      };

    case 'REPORT_READY':
      return {
        ...state,
        reportUrl: action.payload.url
      };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}
