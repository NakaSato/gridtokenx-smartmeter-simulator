/**
 * Centralized API Service
 * Handles all HTTP requests with consistent error handling and response formatting
 */

const API_BASE = window.location.origin;

class ApiService {
  constructor(baseURL = API_BASE) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  /**
   * Generic request handler
   * @param {string} endpoint - API endpoint
   * @param {object} options - Fetch options
   * @returns {Promise<object>} Response data
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || `HTTP ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  /**
   * GET request
   */
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post(endpoint, body = null) {
    return this.request(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : null,
    });
  }

  /**
   * PUT request
   */
  async put(endpoint, body = null) {
    return this.request(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : null,
    });
  }

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // ==================== Simulation Endpoints ====================

  async getStatus() {
    return this.get('/api/status');
  }

  async startSimulation() {
    return this.post('/api/control/start');
  }

  async stopSimulation() {
    return this.post('/api/control/stop');
  }

  async pauseSimulation() {
    return this.post('/api/control/pause');
  }

  async resumeSimulation() {
    return this.post('/api/control/resume');
  }

  async restartSimulation() {
    return this.post('/api/control/restart');
  }

  async updateMeterCount(numMeters) {
    return this.post('/api/control/meters', { num_meters: numMeters });
  }

  // ==================== Meter Endpoints ====================

  async addMeter(meterData) {
    return this.post('/api/meters/add', meterData);
  }

  async deleteMeter(meterId) {
    return this.delete(`/api/meters/${meterId}`);
  }

  async setMeterOverride(meterId, overrideData) {
    return this.post(`/api/meters/${meterId}/override`, overrideData);
  }

  async clearMeterOverride(meterId) {
    return this.delete(`/api/meters/${meterId}/override`);
  }

  // ==================== Grid/Zone Endpoints ====================

  async getZones() {
    return this.get('/api/zones');
  }

  async getThailandData() {
    return this.get('/api/thailand/data');
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
