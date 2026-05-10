import React, { useContext } from 'react';
import { AnalysisContext } from '../../state/analysisContext';
import SectionPanel from '../shared/SectionPanel';

const AIInterpretationPanel = () => {
  const { state } = useContext(AnalysisContext);
  const { status, data, error } = state.results.interpretation;

  const isIdle = state.status === 'idle';
  const panelStatus = isIdle ? 'idle' : status;

  return (
    <SectionPanel title="AI Scientific Interpretation" status={panelStatus} error={error}>
      {panelStatus === 'success' && data && (
        <div className="ai-panel-content">
          <div className="ai-badge-container">
            <span className="source-badge">
              {data.generated_by === 'ai' ? 'OpenRouter AI' : 'Statistical Template'}
            </span>
          </div>
          <blockquote className="ai-summary-block">
            <p>{data.summary}</p>
          </blockquote>
          <div className="ai-disclaimer text-muted">
            <i>This interpretation is generated from statistical data only and should not be used as clinical guidance.</i>
          </div>
        </div>
      )}
    </SectionPanel>
  );
};

export default AIInterpretationPanel;
