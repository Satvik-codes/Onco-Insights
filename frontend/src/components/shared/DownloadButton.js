import React from 'react';

const DownloadButton = ({ url, label, disabled }) => {
  return (
    <button 
      className={`download-button ${disabled ? 'disabled' : ''}`}
      disabled={disabled}
      onClick={() => {
        if (!disabled && url) {
          window.open(url, '_blank');
        }
      }}
    >
      <svg className="download-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span>{label}</span>
    </button>
  );
};

export default DownloadButton;
