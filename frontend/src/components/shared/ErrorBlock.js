import React, { useState } from 'react';

const ErrorBlock = ({ errorCode, message, details }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="error-block">
      <div className="error-code monospace">{errorCode}</div>
      <div className="error-message">{message}</div>
      {details && (
        <div className="error-details-container">
          <button 
            className="error-details-toggle text-muted" 
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Hide Details' : 'Show Details'}
          </button>
          {expanded && (
            <pre className="error-details monospace text-muted">
              {typeof details === 'object' ? JSON.stringify(details, null, 2) : details}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};

export default ErrorBlock;
