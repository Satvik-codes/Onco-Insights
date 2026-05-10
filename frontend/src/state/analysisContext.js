import React, { createContext, useReducer } from 'react';
import { initialState, analysisReducer } from './analysisReducer';

export const AnalysisContext = createContext();

export const AnalysisProvider = ({ children }) => {
  const [state, dispatch] = useReducer(analysisReducer, initialState);

  return (
    <AnalysisContext.Provider value={{ state, dispatch }}>
      {children}
    </AnalysisContext.Provider>
  );
};
