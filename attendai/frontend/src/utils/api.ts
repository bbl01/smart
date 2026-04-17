/**
 * AttendAI API Client
 * Centralised axios instance + typed request helpers
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Axios Instance ──────────────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

// ─── Request Interceptor (JWT) ───────────────────────────────────────────────

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Response Interceptor (Token Refresh) ────────────────────────────────────

let isRefreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);

        refreshQueue.forEach((cb) => cb(data.access_token));
        refreshQueue = [];

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

// ─── Auth API ─────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/auth/me'),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.patch('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
};

// ─── Persons API ──────────────────────────────────────────────────────────────

export const personsApi = {
  list: (params?: {
    type?: string;
    group_id?: string;
    search?: string;
    has_biometrics?: boolean;
    limit?: number;
    offset?: number;
  }) => api.get('/persons', { params }),

  get: (id: string) => api.get(`/persons/${id}`),

  create: (formData: FormData) =>
    api.post('/persons', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  enrollFace: (id: string, photo: File) => {
    const form = new FormData();
    form.append('photo', photo);
    return api.post(`/persons/${id}/enroll-face`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  delete: (id: string) => api.delete(`/persons/${id}`),
};

// ─── Attendance API ───────────────────────────────────────────────────────────

export const attendanceApi = {
  getRecords: (params?: {
    person_id?: string;
    date_from?: string;
    date_to?: string;
    status?: string;
    limit?: number;
  }) => api.get('/attendance', { params }),

  markManual: (data: {
    person_id: string;
    status: string;
    session_id?: string;
    notes?: string;
  }) => api.post('/attendance/manual', data),

  getSessions: (params?: { date?: string; group_id?: string }) =>
    api.get('/attendance/sessions', { params }),
};

// ─── Analytics API ────────────────────────────────────────────────────────────

export const analyticsApi = {
  summary: () => api.get('/analytics/summary'),
  weekly: (weeks?: number) => api.get('/analytics/weekly', { params: { weeks } }),
  heatmap: (month?: number, year?: number) =>
    api.get('/analytics/heatmap', { params: { month, year } }),
  groups: (params?: { date_from?: string; date_to?: string }) =>
    api.get('/analytics/groups', { params }),
  lateArrivals: (days?: number) =>
    api.get('/analytics/late-arrivals', { params: { days } }),
};

// ─── Cameras API ──────────────────────────────────────────────────────────────

export const camerasApi = {
  list: () => api.get('/cameras'),
  get: (id: string) => api.get(`/cameras/${id}`),
  create: (data: {
    name: string;
    location: string;
    rtsp_url: string;
    ip_address?: string;
  }) => api.post('/cameras', data),
  update: (id: string, data: Partial<{ name: string; location: string; rtsp_url: string; is_active: boolean }>) =>
    api.patch(`/cameras/${id}`, data),
  delete: (id: string) => api.delete(`/cameras/${id}`),
  getSnapshot: (id: string) => api.get(`/cameras/${id}/snapshot`, { responseType: 'blob' }),
  restart: (id: string) => api.post(`/cameras/${id}/restart`),
};

// ─── WebSocket ────────────────────────────────────────────────────────────────

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function createWebSocket(): WebSocket {
  const token = localStorage.getItem('access_token');
  const url = `${WS_URL}/api/v1/ws/live${token ? `?token=${token}` : ''}`;
  return new WebSocket(url);
}

export default api;
