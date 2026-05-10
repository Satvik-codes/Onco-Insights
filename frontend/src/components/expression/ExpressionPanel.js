import React, { useContext } from 'react';
import { AnalysisContext } from '../../state/analysisContext';
import SectionPanel from '../shared/SectionPanel';
import StatCard from '../shared/StatCard';
import Badge from '../shared/Badge';
import ExpressionPlot from './ExpressionPlot';

const ExpressionPanel = () => {
  const { state } = useContext(AnalysisContext);
  const { status, data, error } = state.results.expression;

  const isIdle = state.status === 'idle';
  const panelStatus = isIdle ? 'idle' : status;

  return (
    <SectionPanel title="Differential Expression Analysis" status={panelStatus} error={error}>
      {panelStatus === 'success' && data && (
        <div className="panel-content-inner">
          <div className="metrics-row">
            <StatCard 
              label="Fold Change (Linear)" 
              value={data.fold_change ? data.fold_change.toFixed(2) : 'N/A'} 
              significance={data.significant ? 'significant' : 'not-significant'}
            />
            <StatCard 
              label="Log2 Fold Change" 
              value={data.log2_fold_change ? data.log2_fold_change.toFixed(2) : 'N/A'} 
            />
            <StatCard 
              label="p-value" 
              value={data.p_value ? data.p_value.toExponential(2) : 'N/A'} 
              significance={data.significant ? 'significant' : 'not-significant'}
            />
            <StatCard 
              label="Statistical Test" 
              value={data.statistical_test || 'N/A'} 
            />
          </div>
          <div className="badge-row">
            <span className="text-muted">Expression is: </span>
            <Badge 
              type={data.direction || 'unchanged'} 
              label={(data.direction || 'Unchanged').charAt(0).toUpperCase() + (data.direction || 'unchanged').slice(1)} 
            />
          </div>
          <ExpressionPlot plotJson={data.plot_json} />
        </div>
      )}
    </SectionPanel>
  );
};

export default ExpressionPanel;
