/**
 * PIA API Service — handles all backend communication.
 */

const API_BASE = '/api';

class APIService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Don't set Content-Type for FormData
    if (options.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  // Query
  async query(queryText, company = null, docType = null) {
    return this.request('/query', {
      method: 'POST',
      body: JSON.stringify({
        query: queryText,
        company: company || null,
        doc_type: docType || null,
      }),
    });
  }

  // Ingestion
  async ingest(dataDir = null, skipExtraction = false, force = false) {
    const formData = new FormData();
    if (dataDir) formData.append('data_dir', dataDir);
    formData.append('skip_extraction', skipExtraction);
    formData.append('force', force);

    return this.request('/ingest', {
      method: 'POST',
      body: formData,
    });
  }

  async uploadAndIngest(files, docType, company, skipExtraction = false) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    formData.append('doc_type', docType);
    formData.append('company', company);
    formData.append('skip_extraction', skipExtraction);

    return this.request('/ingest/upload', {
      method: 'POST',
      body: formData,
    });
  }

  // Companies
  async getCompanies() {
    return this.request('/companies');
  }

  async getCompanyDetail(name) {
    return this.request(`/companies/${encodeURIComponent(name)}`);
  }

  // Resume
  async analyzeResume(company, resumeFile = null, resumeText = '') {
    const formData = new FormData();
    formData.append('company', company);
    if (resumeFile) formData.append('resume_file', resumeFile);
    if (resumeText) formData.append('resume_text', resumeText);

    return this.request('/resume/analyze', {
      method: 'POST',
      body: formData,
    });
  }

  // Evaluation
  async runEval(modes = ['dense_only', 'hybrid', 'hybrid_reranked'], includeFaithfulness = false) {
    return this.request('/eval/run', {
      method: 'POST',
      body: JSON.stringify({
        modes,
        include_faithfulness: includeFaithfulness,
      }),
    });
  }

  async getEvalResults() {
    return this.request('/eval/results');
  }

  // Stats
  async getStats() {
    return this.request('/stats');
  }

  // Health
  async healthCheck() {
    const response = await fetch('/api/health');
    return response.json();
  }
}

export const api = new APIService();
export default api;
