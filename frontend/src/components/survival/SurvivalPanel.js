import React, { useContext } from 'react';
import { AnalysisContext } from '../../state/analysisContext';
import SectionPanel from '../shared/SectionPanel';
import StatCard from '../shared/StatCard';
import Badge from '../shared/Badge';
import SurvivalPlot from './SurvivalPlot';

const SurvivalPanel = () => {
  const { state } = useContext(AnalysisContext);
  const { status, data, error } = state.results.survival;

  const isIdle = state.status === 'idle';
  const panelStatus = isIdle ? 'idle' : status;

  return (
    <SectionPanel title="Survival Analysis" status={panelStatus} error={error}>
      {panelStatus === 'success' && data && (
        <div className="panel-content-inner">
          <div className="metrics-row">
            <StatCard 
              label="Hazard Ratio" 
              value={data.hazard_ratio ? data.hazard_ratio.toFixed(2) : 'N/A'} 
              significance={data.significant ? 'significant' : 'not-significant'}
            />
            <StatCard 
              label="Log-rank p-value" 
              value={data.logrank_p_value ? data.logrank_p_value.toExponential(2) : 'N/A'} 
              significance={data.significant ? 'significant' : 'not-significant'}
            />
            <StatCard 
              label="Median Survival (High)" 
              value={data.median_survival_high ? Math.round(data.median_survival_high) : 'N/A'} 
              unit="days"
            />
            <StatCard 
              label="Median Survival (Low)" 
              value={data.median_survival_low ? Math.round(data.median_survival_low) : 'N/A'} 
              unit="days"
            />
          </div>
          <div className="badge-row">
            <span className="text-muted">Significance: </span>
            <Badge 
              type={data.significant ? 'significant' : 'not-significant'} 
              label={data.significant ? 'Significant' : 'Not Significant'} 
            />
          </div>
          <SurvivalPlot plotJson={data.plot_json} />
        </div>
      )}
    </SectionPanel>
  );
};

export default SurvivalPanel;
