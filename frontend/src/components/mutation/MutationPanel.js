import React, { useContext } from 'react';
import { AnalysisContext } from '../../state/analysisContext';
import SectionPanel from '../shared/SectionPanel';
import StatCard from '../shared/StatCard';
import Badge from '../shared/Badge';
import MutationFrequencyPlot from './MutationFrequencyPlot';
import MutationTypePlot from './MutationTypePlot';

const MutationPanel = () => {
  const { state } = useContext(AnalysisContext);
  const { status, data, error } = state.results.mutation;

  const isIdle = state.status === 'idle';
  const panelStatus = isIdle ? 'idle' : status;

  return (
    <SectionPanel title="Mutation Profiling" status={panelStatus} error={error}>
      {panelStatus === 'success' && data && (
        <div className="panel-content-inner">
          <div className="metrics-row">
            <StatCard 
              label="Mutation Frequency" 
              value={data.mutation_frequency_percent ? data.mutation_frequency_percent.toFixed(2) : '0'} 
              unit="%" 
            />
            <StatCard 
              label="Cohort Size" 
              value={data.cohort_size || 'N/A'} 
              unit="patients" 
            />
            <StatCard 
              label="Mutated Patients" 
              value={data.mutated_patients || '0'} 
            />
          </div>
          <div className="badge-row">
            <span className="text-muted">Status: </span>
            <Badge 
              type={data.has_mutations ? 'mutated' : 'not-mutated'} 
              label={data.has_mutations ? 'Mutated' : 'Not Detected'} 
            />
          </div>
          
          <div className="plots-grid">
            <div className="plot-col">
              <MutationFrequencyPlot plotJson={data.frequency_plot_json} />
            </div>
            <div className="plot-col">
              <MutationTypePlot plotJson={data.type_plot_json} />
            </div>
          </div>
          
          {data.has_mutations && data.mutation_types && (
            <div className="mutation-table-container">
              <table className="mutation-table">
                <thead>
                  <tr>
                    <th>Mutation Type</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.mutation_types)
                    .filter(([_, count]) => count > 0)
                    .sort((a, b) => b[1] - a[1])
                    .map(([type, count]) => (
                    <tr key={type}>
                      <td>{type}</td>
                      <td className="monospace">{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </SectionPanel>
  );
};

export default MutationPanel;
