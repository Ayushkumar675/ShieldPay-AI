/**
 * ShieldPay AI — API Service Layer
 * Handles all communication with FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

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
  
  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('shieldpay_token');
    localStorage.removeItem('shieldpay_user');
  }

  isAuthenticated() {
    return !!this.token;
  }
  
  getUser() {
    return this.user;
  }

  setAuth(data) {
    this.token = data.access_token;
    this.user = { id: data.user_id, name: data.name, role: data.role };
    localStorage.setItem('shieldpay_token', data.access_token);
    localStorage.setItem('shieldpay_user', JSON.stringify(this.user));
  }

  async login(credentials) {
    const data = await this.request('/workers/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    if (data?.access_token) {
      this.setAuth(data);
    }
    return data;
  }

  async register(userData) {
    const data = await this.request('/workers/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    if (data?.access_token) {
      this.setAuth(data);
    }
    return data;
  }

  // --- Real Endpoints ---

  async getAdminDashboard() {
    return this.request('/analytics/admin-dashboard');
  }

  async getWorkerDashboard(workerId) {
    // If no workerId provided, try to use current user
    const id = workerId || this.user?.id;
    if (!id) return null;
    return this.request(`/analytics/worker-dashboard/${id}`);
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
    return this.getRecentClaims(); // Should filter by user ID on backend ideally
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
    return data || { trend: [], summary: {} };
  }
  
  async getFraudHeatmapAI() {
    const data = await this.request('/analytics/fraud-heatmap');
    return data || { heatmap: [] };
  }

  async getFraudAlertsAI() {
    const data = await this.request('/analytics/fraud-alerts-ai');
    return data || { alerts: [] };
  }

  async getFraudRings() {
    const data = await this.request('/analytics/fraud-rings');
    return data || { fraud_rings: [] };
  }

  async getWorkerForecast(workerId) {
    const id = workerId || this.user?.id;
    if (!id) return null;
    return this.request(`/analytics/worker-forecast/${id}`);
  }

  async getWarehouseRisk() {
    const data = await this.request('/analytics/warehouse-risk');
    return { warehouses: data?.warehouses || [] };
  }
  
  // Policies (existing, keeping simple)
  async getMyPolicy() {
    // Mock for now or implement if needed
    return { policy: { id: "p1", coverage_amount: 5000, status: "active" }}; 
  }
}

export default new ApiService();
