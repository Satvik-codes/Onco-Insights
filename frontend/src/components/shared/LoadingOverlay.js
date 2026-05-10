import React from 'react';

const LoadingOverlay = ({ title }) => {
  return (
    <div className="loading-overlay">
      <div className="loading-animation">
        {/* Shimmer or pulsing line css implementation */}
        <div className="shimmer-line"></div>
      </div>
      <div className="loading-text text-muted monospace">
        Analyzing {title}...
      </div>
    </div>
  );
};

export default LoadingOverlay;
