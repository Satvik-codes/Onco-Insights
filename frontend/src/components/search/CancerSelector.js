import React from 'react';
import config from '../../config';

const CancerSelector = ({ selected, onChange }) => {
  return (
    <div className="cancer-selector">
      {config.supportedCancers.map((cancer) => {
        const isSelected = selected === cancer.code;
        return (
          <div 
            key={cancer.code} 
            className={`cancer-card ${isSelected ? 'selected' : ''}`}
            onClick={() => onChange(cancer.code)}
          >
            <div className="cancer-label">{cancer.label}</div>
            <div className="cancer-code monospace">{cancer.code}</div>
          </div>
        );
      })}
    </div>
  );
};

export default CancerSelector;
