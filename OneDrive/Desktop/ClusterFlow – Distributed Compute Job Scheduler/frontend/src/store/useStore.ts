import { create } from 'zustand';

interface User {
  id: string;
  email: string;
  role: string;
}

export interface AlertMessage {
  id: string;
  jobId: string;
  taskId: string;
  error: string;
  timestamp: string;
}

interface Settings {
  serverUrl: string;
  refreshInterval: number;
  theme: 'dark' | 'light';
}

interface ClusterStore {
  user: User | null;
  token: string | null;
  alerts: AlertMessage[];
  settings: Settings;
  login: (user: User, token: string) => void;
  logout: () => void;
  addAlert: (alert: Omit<AlertMessage, 'id' | 'timestamp'>) => void;
  clearAlerts: () => void;
  updateSettings: (settings: Partial<Settings>) => void;
}

export const useStore = create<ClusterStore>((set) => ({
  user: localStorage.getItem('cf_user') ? JSON.parse(localStorage.getItem('cf_user')!) : null,
  token: localStorage.getItem('cf_token'),
  alerts: [],
  settings: {
    serverUrl: 'http://localhost:8080',
    refreshInterval: 5000,
    theme: 'dark',
  },
  login: (user, token) => {
    localStorage.setItem('cf_user', JSON.stringify(user));
    localStorage.setItem('cf_token', token);
    set({ user, token });
    window.dispatchEvent(new Event('auth_login'));
  },
  logout: () => {
    localStorage.removeItem('cf_user');
    localStorage.removeItem('cf_token');
    set({ user: null, token: null });
    window.dispatchEvent(new Event('auth_logout'));
  },
  addAlert: (alert) => {
    const newAlert: AlertMessage = {
      ...alert,
      id: Math.random().toString(36).substring(7),
      timestamp: new Date().toLocaleTimeString(),
    };
    set((state) => ({ alerts: [newAlert, ...state.alerts].slice(0, 15) }));
  },
  clearAlerts: () => set({ alerts: [] }),
  updateSettings: (newSettings) => set((state) => ({ settings: { ...state.settings, ...newSettings } })),
}));
