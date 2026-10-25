import axios from 'axios';

// Use environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for model inference
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`📤 ${config.method?.toUpperCase()} ${config.url}`, config.data);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for logging
api.interceptors.response.use(
  (response) => {
    console.log(`📥 Response from ${response.config.url}:`, response.status);
    return response;
  },
  (error) => {
    if (error.response) {
      console.error('Response error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ============================================
// API FUNCTIONS
// ============================================

/**
 * Analyze a genetic variant
 * @param {Object} data - Variant data
 * @param {string} data.chromosome - Chromosome (e.g., 'chr17')
 * @param {number} data.position - Genomic position
 * @param {string} data.reference_allele - Reference allele
 * @param {string} data.alternate_allele - Alternate allele
 * @param {string} data.gene - Gene name (BRCA1, TP53, etc.)
 * @returns {Promise} Analysis results
 */
export const analyzeVariant = async (data) => {
  try {
    // Cold analysis includes UCSC exon retrieval and two model requests.
    const response = await api.post('/analyze', data, { timeout: 300000 });
    return response.data;
  } catch (error) {
    if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
      throw new Error('Analysis timed out after 5 minutes. Sequence retrieval or model inference is taking too long; check the backend and Colab logs.');
    } else if (error.response) {
      // Server responded with error
      throw new Error(error.response.data?.detail || `Server error: ${error.response.status}`);
    } else if (error.request) {
      // No response from server
      throw new Error('Network error. Please check if the backend server is running.');
    } else {
      throw new Error(error.message || 'An error occurred during analysis');
    }
  }
};

/**
 * Check backend health
 * @returns {Promise<Object>} Health status
 */
export const healthCheck = async () => {
  try {
    const response = await api.get('/health', { timeout: 15000 });
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return null;
  }
};

/**
 * Get allowed genes
 * @returns {Promise<Array>} List of allowed genes
 */
export const getAllowedGenes = async () => {
  try {
    const response = await api.get('/api/v1/genes');
    return response.data.allowed_genes || ['BRCA1', 'TP53', 'BRCA2'];
  } catch (error) {
    console.error('Failed to get genes:', error);
    return ['BRCA1', 'TP53', 'BRCA2'];
  }
};

// Export the api instance for custom requests
export default api;
