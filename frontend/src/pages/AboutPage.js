import React from 'react';

const AboutPage = () => {
  return (
    <div className="about-page">
      <h2>About Cancer Gene Validation Copilot</h2>
      <p>
        The Cancer Gene Validation Copilot is an exploratory bioinformatics tool 
        designed to assist researchers in evaluating the potential of specific genes 
        as prognostic biomarkers in major cancer types.
      </p>
      
      <h3>Data Sources</h3>
      <ul>
        <li>
          <strong>UCSC Xena Browser:</strong> Expression and clinical data are derived from the TCGA TARGET GTEx study.
        </li>
        <li>
          <strong>cBioPortal:</strong> Mutation data are sourced from TCGA PanCancer Atlas datasets.
        </li>
      </ul>

      <h3>Supported Analyses</h3>
      <p>The platform performs four main types of analysis:</p>
      <ul>
        <li><strong>Differential Expression:</strong> Compares gene expression in tumor vs. normal tissue.</li>
        <li><strong>Survival Analysis:</strong> Evaluates overall survival differences between high and low expression groups.</li>
        <li><strong>Mutation Profiling:</strong> Summarizes mutation frequency and variant types.</li>
        <li><strong>AI Interpretation:</strong> Provides a concise, statistically grounded summary of the results.</li>
      </ul>

      <h3>Limitations & Disclaimer</h3>
      <p className="text-muted">
        <em>
          This tool is for research purposes only. The results are exploratory and have not been clinically validated. 
          It should not be used for medical diagnosis, treatment planning, or clinical decision-making. 
          Statistical significance in these analyses does not imply causation.
        </em>
      </p>
    </div>
  );
};

export default AboutPage;
