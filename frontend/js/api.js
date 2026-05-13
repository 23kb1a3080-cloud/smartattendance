/**
 * API Client Module
 * Covers: API Calls, Async/Await, Fetch, HTTP Methods, JWT Auth
 */

const API_BASE = window.API_BASE || 'http://localhost:8000';

// ─── Token Management ─────────────────────────────────────────────────────────
const Auth = {
  getToken: () => localStorage.getItem('access_token'),
  setToken: (token) => localStorage.setItem('access_token', token),
  removeToken: () => localStorage.removeItem('access_token'),
  getUser: () => {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  },
  setUser: (user) => localStorage.setItem('user', JSON.stringify(user)),
  removeUser: () => localStorage.removeItem('user'),
  isLoggedIn: () => !!localStorage.getItem('access_token'),
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/index.html';
  }
};

// ─── Base Fetch Wrapper ───────────────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
  const token = Auth.getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  // Don't set Content-Type for FormData (file uploads)
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config);

    // Handle 401 - redirect to login
    if (response.status === 401) {
      Auth.logout();
      return null;
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    return data;
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Cannot connect to server. Is the backend running?');
    }
    throw error;
  }
}

// ─── Auth API ─────────────────────────────────────────────────────────────────
const AuthAPI = {
  async login(username, password) {
    const data = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (data) {
      Auth.setToken(data.access_token);
      Auth.setUser(data.user);
    }
    return data;
  },

  async signup(userData) {
    return apiFetch('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  async getMe() {
    return apiFetch('/api/auth/me');
  },

  async logout() {
    await apiFetch('/api/auth/logout', { method: 'POST' });
    Auth.logout();
  },

  async listUsers() {
    return apiFetch('/api/auth/users');
  }
};

// ─── Students API ─────────────────────────────────────────────────────────────
const StudentsAPI = {
  async list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiFetch(`/api/students/${query ? '?' + query : ''}`);
  },

  async get(rollNo) {
    return apiFetch(`/api/students/${rollNo}`);
  },

  async create(studentData) {
    return apiFetch('/api/students/', {
      method: 'POST',
      body: JSON.stringify(studentData),
    });
  },

  async update(rollNo, updateData) {
    return apiFetch(`/api/students/${rollNo}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  },

  async delete(rollNo) {
    return apiFetch(`/api/students/${rollNo}`, { method: 'DELETE' });
  },

  async uploadFace(rollNo, file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiFetch(`/api/students/${rollNo}/upload-face`, {
      method: 'POST',
      body: formData,
    });
  },

  async listDepartments() {
    return apiFetch('/api/students/departments');
  },

  async createDepartment(deptData) {
    return apiFetch('/api/students/departments', {
      method: 'POST',
      body: JSON.stringify(deptData),
    });
  }
};

// ─── Attendance API ───────────────────────────────────────────────────────────
const AttendanceAPI = {
  async list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiFetch(`/api/attendance/${query ? '?' + query : ''}`);
  },

  async today() {
    return apiFetch('/api/attendance/today');
  },

  async stats() {
    return apiFetch('/api/attendance/stats');
  },

  async mark(data) {
    return apiFetch('/api/attendance/mark', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async studentHistory(rollNo) {
    return apiFetch(`/api/attendance/student/${rollNo}`);
  },

  async delete(id) {
    return apiFetch(`/api/attendance/${id}`, { method: 'DELETE' });
  },

  async exportJson(date = null) {
    const query = date ? `?date=${date}` : '';
    return apiFetch(`/api/attendance/export/json${query}`);
  }
};

// ─── Dashboard API ────────────────────────────────────────────────────────────
const DashboardAPI = {
  async summary() {
    return apiFetch('/api/dashboard/summary');
  },

  async logs(limit = 50) {
    return apiFetch(`/api/dashboard/logs?limit=${limit}`);
  },

  async weeklyReport() {
    return apiFetch('/api/dashboard/weekly-report');
  }
};

// ─── WebSocket: Real-time Attendance ─────────────────────────────────────────
class LiveAttendance {
  constructor(onMessage) {
    this.onMessage = onMessage;
    this.ws = null;
    this.reconnectDelay = 3000;
  }

  connect() {
    const wsUrl = API_BASE.replace('http', 'ws') + '/api/dashboard/ws/live';
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.onMessage({ type: 'connected' });
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...');
        setTimeout(() => this.connect(), this.reconnectDelay);
      };

      this.ws.onerror = (err) => {
        console.warn('WebSocket error:', err);
      };
    } catch (e) {
      console.warn('WebSocket not available');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

// ─── UI Helpers ───────────────────────────────────────────────────────────────
const UI = {
  showToast(message, type = 'info', duration = 3500) {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  showLoading(btn, text = 'Loading...') {
    btn.disabled = true;
    btn._originalText = btn.innerHTML;
    btn.innerHTML = `<div class="spinner"></div> ${text}`;
  },

  hideLoading(btn) {
    btn.disabled = false;
    btn.innerHTML = btn._originalText || 'Submit';
  },

  formatDate(dateStr) {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric'
    });
  },

  formatTime(timeStr) {
    if (!timeStr) return '-';
    return timeStr.substring(0, 5);
  },

  formatConfidence(val) {
    if (val == null) return '-';
    return `${(val * 100).toFixed(1)}%`;
  },

  requireAuth() {
    if (!Auth.isLoggedIn()) {
      window.location.href = '/index.html';
      return false;
    }
    return true;
  },

  updateNavUser() {
    const user = Auth.getUser();
    if (!user) return;
    const el = document.getElementById('nav-user-name');
    const av = document.getElementById('nav-user-avatar');
    if (el) el.textContent = user.full_name || user.username;
    if (av) av.textContent = (user.full_name || user.username)[0].toUpperCase();
  }
};

// Export for use in other scripts
window.Auth = Auth;
window.AuthAPI = AuthAPI;
window.StudentsAPI = StudentsAPI;
window.AttendanceAPI = AttendanceAPI;
window.DashboardAPI = DashboardAPI;
window.LiveAttendance = LiveAttendance;
window.UI = UI;
