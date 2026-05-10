import React, { useContext } from 'react';
import { AnalysisContext } from '../../state/analysisContext';
import StatCard from '../shared/StatCard';
import Badge from '../shared/Badge';

const SummaryMetricsBar = () => {
  const { state } = useContext(AnalysisContext);
  const { status, results } = state;

  if (status === 'idle' || status === 'loading') {
    return null;
  }

  const { expression, survival, mutation, interpretation } = results;

  return (
    <div className="summary-metrics-bar">
      <StatCard 
        label="Log2 Fold Change" 
        value={expression.status === 'success' && expression.data ? expression.data.log2_fold_change.toFixed(2) : 'N/A'} 
        significance={expression.status === 'success' && expression.data?.significant ? 'significant' : 'not-significant'}
      />
      <div className="stat-card">
        <div className="stat-label text-muted">Hazard Ratio</div>
        <div className={`stat-value monospace ${survival.status === 'success' && survival.data?.significant ? 'text-significant' : 'text-not-significant'}`}>
          {survival.status === 'success' && survival.data ? survival.data.hazard_ratio.toFixed(2) : 'N/A'}
        </div>
        {survival.status === 'success' && survival.data?.hr_confidence_interval && (
          <div className="stat-unit text-muted" style={{ fontSize: '10px' }}>
            95% CI: [{survival.data.hr_confidence_interval[0].toFixed(2)}, {survival.data.hr_confidence_interval[1].toFixed(2)}]
          </div>
        )}
      </div>
      <StatCard 
        label="Mutation Frequency" 
        value={mutation.status === 'success' && mutation.data ? mutation.data.mutation_frequency_percent.toFixed(2) : 'N/A'} 
        unit="%"
      />
      <div className="stat-card">
        <div className="stat-label text-muted">AI Summary Status</div>
        <div className="stat-value" style={{ fontSize: '14px', marginTop: '4px' }}>
          {interpretation.status === 'success' && interpretation.data ? (
             <Badge type="mutated" label={interpretation.data.generated_by === 'ai' ? 'AI Interpreted' : 'Template Generated'} />
          ) : 'N/A'}
        </div>
      </div>
    </div>
  );
};

export default SummaryMetricsBar;
