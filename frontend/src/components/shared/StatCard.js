import React from 'react';

const StatCard = ({ label, value, unit, significance }) => {
  let valueClass = '';
  if (significance === 'significant') valueClass = 'text-significant';
  if (significance === 'not-significant') valueClass = 'text-not-significant';
  
  return (
    <div className="stat-card">
      <div className="stat-label text-muted">{label}</div>
      <div className={`stat-value ${valueClass} monospace`}>
        {value} {unit && <span className="stat-unit">{unit}</span>}
      </div>
    </div>
  );
};

export default StatCard;
