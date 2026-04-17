/**
 * Zustand store — глобальное состояние приложения
 */
import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'teacher' | 'staff' | 'viewer';
  is_active: boolean;
  last_login: string | null;
}

export interface AttendanceSummary {
  present_now: number;
  total_registered: number;
  attendance_rate: number;
  alerts_today: number;
  by_type: Record<string, number>;
  date: string;
}

export interface LiveEvent {
  id: string;
  type: 'face_detected' | 'camera_status' | 'alert';
  camera_id?: string;
  person_id?: string;
  person_name?: string;
  confidence?: number;
  is_known?: boolean;
  status?: string;
  message?: string;
  timestamp: string;
}

export interface CameraStatus {
  id: string;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'error' | 'maintenance';
  persons_detected: number;
}

// ─── Auth Store ───────────────────────────────────────────────────────────────

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    devtools(
      (set) => ({
        user: null,
        isAuthenticated: false,
        accessToken: null,
        refreshToken: null,

        setAuth: (user, accessToken, refreshToken) => {
          localStorage.setItem('access_token', accessToken);
          localStorage.setItem('refresh_token', refreshToken);
          set({ user, isAuthenticated: true, accessToken, refreshToken });
        },

        logout: () => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          set({ user: null, isAuthenticated: false, accessToken: null, refreshToken: null });
        },
      }),
      { name: 'auth-store' },
    ),
    {
      name: 'attendai-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
);

// ─── Dashboard Store ──────────────────────────────────────────────────────────

interface DashboardState {
  summary: AttendanceSummary | null;
  liveEvents: LiveEvent[];
  cameraStatuses: Record<string, CameraStatus>;
  wsConnected: boolean;

  setSummary: (summary: AttendanceSummary) => void;
  addLiveEvent: (event: LiveEvent) => void;
  updateCameraStatus: (cameraId: string, status: Partial<CameraStatus>) => void;
  setWsConnected: (connected: boolean) => void;
  clearEvents: () => void;
}

const MAX_LIVE_EVENTS = 100;

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set) => ({
      summary: null,
      liveEvents: [],
      cameraStatuses: {},
      wsConnected: false,

      setSummary: (summary) => set({ summary }),

      addLiveEvent: (event) =>
        set((state) => ({
          liveEvents: [event, ...state.liveEvents].slice(0, MAX_LIVE_EVENTS),
        })),

      updateCameraStatus: (cameraId, status) =>
        set((state) => ({
          cameraStatuses: {
            ...state.cameraStatuses,
            [cameraId]: { ...state.cameraStatuses[cameraId], ...status },
          },
        })),

      setWsConnected: (wsConnected) => set({ wsConnected }),

      clearEvents: () => set({ liveEvents: [] }),
    }),
    { name: 'dashboard-store' },
  ),
);

// ─── UI Store ─────────────────────────────────────────────────────────────────

interface UiState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'system',

      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'attendai-ui' },
  ),
);
