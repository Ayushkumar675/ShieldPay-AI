/**
 * ShieldPay AI — API Service Layer
 * Handles all communication with FastAPI backend.
 */

const API_BASE = 'http://localhost:8000/api/v1'; // Hardcoded for simplified demo, typically process.env

class ApiService {
  constructor() {
    this.token = localStorage.getItem('shieldpay_token');
    this.user = JSON.parse(localStorage.getItem('shieldpay_user') || 'null');
  }

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: this.getHeaders(),
      });
      if (res.status === 401) {
        // Handle auth logic
        return null;
      }
      return await res.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      return null;
    }
  }

  // --- Real Endpoints ---

  async getAdminDashboard() {
    return this.request('/analytics/admin-dashboard');
  }

  async getWorkerDashboard(workerId) {
    return this.request(`/analytics/worker-dashboard/${workerId}`);
  }

  async getActiveDisruptions() {
    const data = await this.request('/analytics/disruptions');
    return { disruptions: data || [] };
  }
  
  // Method compatibility for existing components
  async getActiveDisruptionsAI() {
    return this.getActiveDisruptions();
  }

  async simulateDisruption(type, city) {
    return this.request('/simulation/simulate-disruption', {
      method: 'POST',
      body: JSON.stringify({ type, city, severity: 0.85 })
    });
  }

  async getRecentClaims() {
    const data = await this.request('/claims');
    return { claims: data || [] };
  }

  async getAllClaims() {
    return this.getRecentClaims();
  }

  async getMyClaims() {
    return this.getRecentClaims();
  }

  async confirmClaim(claimId) {
    return this.request(`/claims/${claimId}/confirm`, {
      method: 'POST'
    });
  }

  async getFraudAnalytics() {
     return this.request('/analytics/admin-dashboard');
  }

  async getFinancialTrend() {
    const data = await this.request('/analytics/financial-trend');
    // Adapt existing UI to new response if needed
    return { trend: data, summary: {} };
  }
  
  async getFraudHeatmapAI() {
    const data = await this.request('/analytics/fraud-heatmap');
    return { heatmap: data?.heatmap || [] };
  }

  async getWarehouseRisk() {
    const data = await this.request('/analytics/warehouse-risk');
    return { warehouses: data?.warehouses || [] };
  }
}

export default new ApiService();
