import React, { useState, useEffect } from 'react';
import { useAnalysis } from '../hooks/useAnalysis';
import GeneSearchBar from '../components/search/GeneSearchBar';
import CancerSelector from '../components/search/CancerSelector';
import SummaryMetricsBar from '../components/metrics/SummaryMetricsBar';
import ExpressionPanel from '../components/expression/ExpressionPanel';
import SurvivalPanel from '../components/survival/SurvivalPanel';
import MutationPanel from '../components/mutation/MutationPanel';
import AIInterpretationPanel from '../components/interpretation/AIInterpretationPanel';
import DownloadButton from '../components/shared/DownloadButton';

const DashboardPage = () => {
  const { query, status, runAnalysis, reportUrl } = useAnalysis();
  const [gene, setGene] = useState(query.gene || '');
  const [cancer, setCancer] = useState(query.cancer || '');
  const [isValid, setIsValid] = useState(false);

  const handleRunAnalysis = () => {
    if (isValid && gene && cancer) {
      runAnalysis(gene, cancer);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="search-section">
        <div className="search-controls">
          <GeneSearchBar 
            value={gene} 
            onChange={setGene} 
            cancerType={cancer} 
            onValidation={setIsValid} 
          />
          <CancerSelector 
            selected={cancer} 
            onChange={setCancer} 
          />
          <button 
            className="btn-primary run-analysis-btn" 
            onClick={handleRunAnalysis}
            disabled={!isValid || !gene || !cancer || status === 'loading'}
          >
            {status === 'loading' ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      </div>

      <SummaryMetricsBar />

      <div className="analysis-grid">
        <div className="grid-row top-row">
          <ExpressionPanel />
          <SurvivalPanel />
        </div>
        <div className="grid-row bottom-row">
          <MutationPanel />
        </div>
        <div className="grid-row bottom-row">
          <AIInterpretationPanel />
        </div>
      </div>

      <div className="report-download-row">
        <DownloadButton 
          url={reportUrl} 
          label={reportUrl ? "Download PDF Report" : "Report generating..."} 
          disabled={!reportUrl} 
        />
      </div>
    </div>
  );
};

export default DashboardPage;
