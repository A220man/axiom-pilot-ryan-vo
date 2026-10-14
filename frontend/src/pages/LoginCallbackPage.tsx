/** Login callback page - handles OIDC redirect. */
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '@/api/client';

export function LoginCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function handleCallback() {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const err = searchParams.get('error');
      const errDesc = searchParams.get('error_description');

      if (err) {
        setStatus('error');
        setError(`${err}: ${errDesc || 'Unknown error'}`);
        return;
      }

      if (!code || !state) {
        // Not a callback, redirect to login
        navigate('/login');
        return;
      }

      try {
        // The backend handles the callback and sets cookies
        // We just need to wait for redirect from backend
        // Actually, the backend redirects to frontend with session cookie
        // So this page might not even be reached if backend redirects directly
        // But we handle it just in case
        await api.auth.me();
        setStatus('success');
        // Redirect to dashboard or intended page
        const redirectAfter = searchParams.get('redirect_after') || '/dashboard';
        navigate(redirectAfter, { replace: true });
      } catch (e) {
        setStatus('error');
        setError(e instanceof Error ? e.message : 'Authentication failed');
      }
    }

    handleCallback();
  }, [searchParams, navigate]);

  if (status === 'loading') {
    return (
      <div className="app">
        <main className="main" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div className="loading" role="status" aria-label="Completing sign in">
            <div className="spinner" />
            <span style={{ marginLeft: '16px' }}>Completing sign in...</span>
          </div>
        </main>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="app">
        <main className="main" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div className="card" style={{ maxWidth: '400px', textAlign: 'center' }}>
            <div className="alert alert-error">{error}</div>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '24px' }}>
              Please try signing in again.
            </p>
            <a href="/login" className="btn btn-primary">Try Again</a>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <main className="main" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div className="card" style={{ maxWidth: '400px', textAlign: 'center' }}>
          <div className="badge badge-success" style={{ marginBottom: '16px' }}>Signed in successfully</div>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: '24px' }}>
            Redirecting to dashboard...
          </p>
          <div className="loading"><div className="spinner" /></div>
        </div>
      </main>
    </div>
  );
}