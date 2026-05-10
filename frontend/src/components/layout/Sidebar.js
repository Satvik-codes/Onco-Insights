import React, { useContext } from 'react';
import { AnalysisContext } from '../../state/analysisContext';

const Sidebar = () => {
  const { state } = useContext(AnalysisContext);
  const { query, lastAnalyzedAt, status } = state;

  return (
    <aside className="sidebar">
      <div className="sidebar-content">
        <h3>Current Analysis</h3>
        <div className="sidebar-info-block">
          <div className="info-label text-muted">Gene</div>
          <div className="info-value monospace">{query.gene || 'None'}</div>
        </div>
        <div className="sidebar-info-block">
          <div className="info-label text-muted">Cancer Type</div>
          <div className="info-value">{query.cancer || 'None'}</div>
        </div>
        
        {lastAnalyzedAt && (
          <div className="sidebar-info-block">
            <div className="info-label text-muted">Last Updated</div>
            <div className="info-value">{new Date(lastAnalyzedAt).toLocaleTimeString()}</div>
          </div>
        )}
        
        <div className="sidebar-legend">
          <h4>Significance Legend</h4>
          <div className="legend-item"><span className="legend-color color-significant"></span> Significant (p≤0.05)</div>
          <div className="legend-item"><span className="legend-color color-warning"></span> Not Significant</div>
          <div className="legend-item"><span className="legend-color color-mutated"></span> Mutated</div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
