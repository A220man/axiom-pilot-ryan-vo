/** React hooks for authentication state. */
import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import { api, type User } from '@/api/client';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: Error | null;
  login: (redirectAfter?: string) => void;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchUser = useCallback(async () => {
    try {
      setError(null);
      const data = await api.auth.me();
      setUser(data);
    } catch (err) {
      setUser(null);
      if (err instanceof Error && err.message !== 'HTTP 401') {
        setError(err);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback((redirectAfter?: string) => {
    api.auth.login(redirectAfter);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } finally {
      setUser(null);
      window.location.href = '/';
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    await fetchUser();
  }, [fetchUser]);

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}