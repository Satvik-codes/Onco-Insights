import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const applyDarkTheme = (plotJson) => {
  if (!plotJson) return null;
  const parsed = typeof plotJson === 'string' ? JSON.parse(plotJson) : JSON.parse(JSON.stringify(plotJson));
  
  parsed.layout = {
    ...parsed.layout,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#ffffff' },
    xaxis: { ...parsed.layout.xaxis, gridcolor: '#2a2f3a', tickfont: { color: '#8b949e' } },
    yaxis: { ...parsed.layout.yaxis, gridcolor: '#2a2f3a', tickfont: { color: '#8b949e' } },
    margin: { l: 20, r: 20, t: 40, b: 40 }
  };
  return parsed;
};

const MutationFrequencyPlot = ({ plotJson }) => {
  const plotData = useMemo(() => applyDarkTheme(plotJson), [plotJson]);

  if (!plotData) return null;

  return (
    <div className="plot-container">
      <Plot
        data={plotData.data}
        layout={plotData.layout}
        config={{ responsive: true, displayModeBar: false }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%', minHeight: '300px' }}
      />
    </div>
  );
};

export default MutationFrequencyPlot;
