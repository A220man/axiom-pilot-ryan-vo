/** Frontend App component tests. */
/// <reference types="vitest" />
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import App from '../App';
import { api } from '../api/client';
// Mock the API client
vi.mock('../api/client', () => ({
  api: {
    auth: {
      me: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
      csrf: vi.fn(),
    },
    health: {
      check: vi.fn(),
      ready: vi.fn(),
    },
  },
}));

const mockApi = vi.mocked(api, { deep: true });

function renderApp() {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders home page when not authenticated', async () => {
    mockApi.auth.me.mockRejectedValue(new Error('HTTP 401'));
    mockApi.health.check.mockResolvedValue({
      status: 'ok',
      app: 'axiom-pilot-ryan-vo',
      version: '1.0.0',
      environment: 'development',
    });

    renderApp();

    await waitFor(() => {
      expect(screen.getByText('AI/ML Developer Tool for Cursor Plugin Quality')).toBeInTheDocument();
    });
  });

  it('shows login button when not authenticated', async () => {
    mockApi.auth.me.mockRejectedValue(new Error('HTTP 401'));

    renderApp();

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
    });
  });

  it('renders dashboard when authenticated', async () => {
    mockApi.auth.me.mockResolvedValue({
      id: 1,
      sub: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
      preferred_username: 'testuser',
      roles: ['viewer'],
    });
    mockApi.health.check.mockResolvedValue({
      status: 'ok',
      app: 'axiom-pilot-ryan-vo',
      version: '1.0.0',
      environment: 'development',
    });
    mockApi.health.ready.mockResolvedValue({
      status: 'ready',
      database: 'connected',
      app: 'axiom-pilot-ryan-vo',
      version: '1.0.0',
    });

    renderApp();

    // Navigate to dashboard
    window.history.pushState({}, '', '/dashboard');
    window.dispatchEvent(new PopStateEvent('popstate'));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Your Account' })).toBeInTheDocument();
    });
  });

  it('shows 404 for unknown routes', async () => {
    mockApi.auth.me.mockRejectedValue(new Error('HTTP 401'));

    renderApp();

    // Navigate to unknown route
    window.history.pushState({}, '', '/unknown-route');
    window.dispatchEvent(new PopStateEvent('popstate'));

    await waitFor(() => {
      expect(screen.getByText('Page Not Found')).toBeInTheDocument();
    });
  });
});