const config = {
  apiBaseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  supportedCancers: [
    { label: "Breast Invasive Carcinoma", code: "BRCA" },
    { label: "Lung Adenocarcinoma", code: "LUAD" },
    { label: "Colon Adenocarcinoma", code: "COAD" }
  ],
  reportPollingIntervalMs: 5000,
  showAboutPage: process.env.REACT_APP_SHOW_ABOUT_PAGE === 'true' || true
};

export default config;
