/**
 * ShieldPay AI — API Service Layer
 * Handles all communication with FastAPI backend.
 */

const API_BASE = '/api/v1';

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
        this.logout();
        window.location.href = '/';
        return null;
      }
      return await res.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      return null;
    }
  }

  setAuth(data) {
    this.token = data.access_token;
    this.user = { id: data.user_id, name: data.name, role: data.role };
    localStorage.setItem('shieldpay_token', data.access_token);
    localStorage.setItem('shieldpay_user', JSON.stringify(this.user));
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

  isAdmin() {
    return this.user?.role === 'admin';
  }

  // ─── Auth ──────────────────────────────────
  async register(data) {
    return this.request('/workers/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(data) {
    return this.request('/workers/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ─── Worker ────────────────────────────────
  async getDashboard() {
    return this.request('/workers/dashboard');
  }

  async getProfile() {
    return this.request('/workers/me');
  }

  async listWorkers(skip = 0, limit = 50) {
    return this.request(`/workers/list?skip=${skip}&limit=${limit}`);
  }

  // ─── Policies ──────────────────────────────
  async purchasePolicy(data) {
    return this.request('/policies/purchase', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getActivePolicy() {
    return this.request('/policies/active');
  }

  async getPolicyHistory() {
    return this.request('/policies/history');
  }

  // ─── Claims ────────────────────────────────
  async submitClaim(triggerId) {
    return this.request(`/claims/submit?trigger_id=${triggerId}`, {
      method: 'POST',
    });
  }

  async getMyClaims() {
    return this.request('/claims/my-claims');
  }

  async getAllClaims(status = null) {
    const qs = status ? `?status_filter=${status}` : '';
    return this.request(`/claims/all${qs}`);
  }

  async confirmClaim(claimId) {
    return this.request(`/claims/${claimId}/confirm?confirmed=true`, {
      method: 'POST',
    });
  }

  // ─── Premium ───────────────────────────────
  async getPremiumQuote() {
    return this.request('/premium/calculate');
  }

  async getPremiumFactors() {
    return this.request('/premium/factors');
  }

  // ─── Fraud ─────────────────────────────────
  async getTrustScore(workerId) {
    return this.request(`/fraud/trust-score/${workerId}`);
  }

  async getFraudAlerts(severityMin = 0) {
    return this.request(`/fraud/alerts?severity_min=${severityMin}`);
  }

  async getFraudRings() {
    return this.request('/fraud/rings');
  }

  async getFraudHeatmap() {
    return this.request('/fraud/heatmap');
  }

  async getFraudAnalytics() {
    return this.request('/fraud/analytics');
  }

  // ─── Integrations ─────────────────────────
  async getWeather(city) {
    return this.request(`/integrations/weather/${city}`);
  }

  async getTraffic(city) {
    return this.request(`/integrations/traffic/${city}`);
  }

  async getActiveDisruptions() {
    return this.request('/integrations/disruptions/active');
  }

  // ─── Payments ──────────────────────────────
  async getPaymentHistory() {
    return this.request('/payments/history');
  }

  async getPlatformPaymentSummary() {
    return this.request('/payments/platform-summary');
  }

  // ─── AI Intelligence ──────────────────────
  async predictRisk(data) {
    return this.request('/ai/predict-risk', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async predictIncomeLoss(data) {
    return this.request('/ai/predict-income-loss', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async detectFraud(data) {
    return this.request('/ai/detect-fraud', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async calculateTrustScore(data) {
    return this.request('/ai/calculate-trust-score', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async calculatePremium(data) {
    return this.request('/ai/calculate-premium', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getActiveDisruptionsAI() {
    return this.request('/ai/active-disruptions');
  }

  async getFinancialTrend() {
    return this.request('/ai/financial-trend');
  }

  async getFraudHeatmapAI() {
    return this.request('/ai/fraud-heatmap');
  }

  async getWarehouseRisk() {
    return this.request('/ai/warehouse-risk');
  }

  async simulateDisruption(type, city = 'Mumbai') {
    return this.request('/ai/simulate-disruption', {
      method: 'POST',
      body: JSON.stringify({ type, city }),
    });
  }

  async getRecentClaims() {
    return this.request('/ai/recent-claims');
  }

  async getFraudAlertsAI() {
    return this.request('/ai/fraud-alerts');
  }
}

export const api = new ApiService();
export default api;

