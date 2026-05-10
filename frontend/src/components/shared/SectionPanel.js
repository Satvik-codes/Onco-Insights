import React from 'react';
import LoadingOverlay from './LoadingOverlay';
import ErrorBlock from './ErrorBlock';

const SectionPanel = ({ title, status, error, children }) => {
  return (
    <div className="section-panel">
      <div className="section-header">
        <h3>{title}</h3>
      </div>
      <div className="section-content">
        {status === 'idle' && (
          <div className="placeholder-message text-muted">
            Run an analysis to view {title.toLowerCase()} results.
          </div>
        )}
        
        {status === 'loading' && <LoadingOverlay title={title} />}
        
        {status === 'error' && error && (
          <ErrorBlock 
            errorCode={error.error_code || 'ERROR'} 
            message={error.message || 'An error occurred'} 
            details={error.details} 
          />
        )}
        
        {status === 'success' && children}
      </div>
    </div>
  );
};

export default SectionPanel;
