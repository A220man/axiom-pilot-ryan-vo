/** Typed API client derived from backend routes. */

type RequestOptions = RequestInit & {
  params?: Record<string, string | number | boolean | undefined>;
};

function buildUrl(path: string, params?: RequestOptions['params']): string {
  const url = new URL(path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  return url.pathname + url.search;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...fetchOptions } = options;

  const response = await fetch(buildUrl(path, params), {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    credentials: 'include', // Include cookies for session auth
  });

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // Use status text if no JSON body
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  // Health
  health: {
    check: () => request<{ status: string; app: string; version: string; environment: string }>('/healthz'),
    ready: () => request<{ status: string; database: string; app: string; version: string }>('/healthz/ready'),
  },

  // Auth
  auth: {
    login: (redirectAfter?: string) => {
      window.location.href = `/auth/login${redirectAfter ? `?redirect_after=${encodeURIComponent(redirectAfter)}` : ''}`;
    },
    logout: () => request<{ logout_url: string; message: string }>('/auth/logout', { method: 'POST' }),
    me: () => request<{
      id: number;
      sub: string;
      email: string;
      name: string;
      preferred_username: string | null;
      roles: string[];
    }>('/auth/me'),
    csrf: () => request<{ csrf_token: string }>('/auth/csrf', { method: 'POST' }),
  },

  // Generic helpers
  get: <T>(path: string, params?: RequestOptions['params']) => request<T>(path, { method: 'GET', params }),
  post: <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};

// Types
export interface User {
  id: number;
  sub: string;
  email: string;
  name: string;
  preferred_username: string | null;
  roles: string[];
}

export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
}

export interface ReadinessStatus {
  status: string;
  database: string;
  app: string;
  version: string;
}