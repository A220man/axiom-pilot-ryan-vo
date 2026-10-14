/** Dashboard page - authenticated user area. */
import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { api, type HealthStatus, type ReadinessStatus } from '@/api/client';

export function DashboardPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [ready, setReady] = useState<ReadinessStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const [h, r] = await Promise.all([api.health.check(), api.health.ready()]);
        setHealth(h);
        setReady(r);
      } catch (err) {
        console.error('Failed to fetch status:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchStatus();
  }, []);

  return (
    <div>
      <header style={{ marginBottom: '32px' }}>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Welcome back, {user?.name}. System status and plugin quality tools.
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <article className="card">
          <div className="card-header">
            <h2 className="card-title">Backend Health</h2>
          </div>
          {loading ? (
            <div className="loading"><div className="spinner" /></div>
          ) : health ? (
            <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px', fontSize: '14px' }}>
              <dt style={{ color: 'var(--color-text-muted)' }}>Status</dt>
              <dd><span className={`badge ${health.status === 'ok' ? 'badge-success' : 'badge-error'}`}>{health.status}</span></dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Application</dt>
              <dd>{health.app}</dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Version</dt>
              <dd>{health.version}</dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Environment</dt>
              <dd>{health.environment}</dd>
            </dl>
          ) : (
            <div className="alert alert-error">Failed to load health status</div>
          )}
        </article>

        <article className="card">
          <div className="card-header">
            <h2 className="card-title">Readiness</h2>
          </div>
          {loading ? (
            <div className="loading"><div className="spinner" /></div>
          ) : ready ? (
            <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px', fontSize: '14px' }}>
              <dt style={{ color: 'var(--color-text-muted)' }}>Status</dt>
              <dd><span className={`badge ${ready.status === 'ready' ? 'badge-success' : 'badge-warning'}`}>{ready.status}</span></dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Database</dt>
              <dd><span className={`badge ${ready.database === 'connected' ? 'badge-success' : 'badge-error'}`}>{ready.database}</span></dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Application</dt>
              <dd>{ready.app}</dd>
              <dt style={{ color: 'var(--color-text-muted)' }}>Version</dt>
              <dd>{ready.version}</dd>
            </dl>
          ) : (
            <div className="alert alert-error">Failed to load readiness</div>
          )}
        </article>

        <article className="card">
          <div className="card-header">
            <h2 className="card-title">Your Account</h2>
          </div>
          <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px', fontSize: '14px' }}>
            <dt style={{ color: 'var(--color-text-muted)' }}>Name</dt>
            <dd>{user?.name}</dd>
            <dt style={{ color: 'var(--color-text-muted)' }}>Email</dt>
            <dd>{user?.email}</dd>
            <dt style={{ color: 'var(--color-text-muted)' }}>Username</dt>
            <dd>{user?.preferred_username || '—'}</dd>
            <dt style={{ color: 'var(--color-text-muted)' }}>Roles</dt>
            <dd>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {user?.roles.map((r, i) => (
                  <span key={i} className="badge badge-info">{r}</span>
                ))}
              </div>
            </dd>
          </dl>
        </article>
      </div>

      <section>
        <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>Plugin Quality Tools</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
          <article className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>Plugin Manifest Validator</h3>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '16px', fontSize: '14px' }}>
              Validate plugin.json, SKILL.md frontmatter, agents/, skills/, hooks/, mcp.json paths.
            </p>
            <button className="btn btn-outline" disabled>Coming Soon</button>
          </article>

          <article className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>Diff Quality Analyzer</h3>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '16px', fontSize: '14px' }}>
              Detect import filtering and whitespace collapsing bugs in PR review renderers.
            </p>
            <button className="btn btn-outline" disabled>Coming Soon</button>
          </article>

          <article className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>OAuth Scope Auditor</h3>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '16px', fontSize: '14px' }}>
              Audit declared OAuth scopes vs required API scopes for MCP connectors.
            </p>
            <button className="btn btn-outline" disabled>Coming Soon</button>
          </article>

          <article className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>Symlink Detector</h3>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '16px', fontSize: '14px' }}>
              Scan for symlinked local plugins that won't load in Cursor.
            </p>
            <button className="btn btn-outline" disabled>Coming Soon</button>
          </article>
        </div>
      </section>
    </div>
  );
}