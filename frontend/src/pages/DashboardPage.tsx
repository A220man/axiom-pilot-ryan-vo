/** Dashboard page - authenticated user area. */
import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { api, type HealthStatus, type ReadinessStatus, type SymlinkIssue } from '@/api/client';

export function DashboardPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [ready, setReady] = useState<ReadinessStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // Symlink detector state
  const [symlinkScanLoading, setSymlinkScanLoading] = useState(false);
  const [symlinkScanResult, setSymlinkScanResult] = useState<{
    scanned_path: string;
    total_plugins: number;
    symlinked_plugins: string[];
    broken_symlinks: string[];
    issues: SymlinkIssue[];
    has_issues: boolean;
    has_symlinks: boolean;
    has_broken: boolean;
  } | null>(null);
  const [symlinkScanError, setSymlinkScanError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const [healthRes, readyRes] = await Promise.all([
          api.health.check(),
          api.health.ready(),
        ]);
        setHealth(healthRes);
        setReady(readyRes);
      } catch (err) {
        console.error('Failed to fetch status:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchStatus();
  }, []);

  const handleSymlinkScan = async () => {
    setSymlinkScanLoading(true);
    setSymlinkScanError(null);
    try {
      const result = await api.symlinks.scan();
      setSymlinkScanResult(result);
    } catch (err) {
      setSymlinkScanError(err instanceof Error ? err.message : 'Failed to scan for symlinks');
    } finally {
      setSymlinkScanLoading(false);
    }
  };

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
            <button 
              className="btn btn-primary" 
              onClick={handleSymlinkScan}
              disabled={symlinkScanLoading}
              style={{ marginBottom: '16px', width: '100%' }}
            >
              {symlinkScanLoading ? 'Scanning...' : 'Scan for Symlinks'}
            </button>
            
            {symlinkScanError && (
              <div className="alert alert-error" style={{ marginBottom: '16px' }}>
                {symlinkScanError}
              </div>
            )}

            {symlinkScanResult && (
              <div style={{ fontSize: '14px' }}>
                <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px', marginBottom: '16px' }}>
                  <dt style={{ color: 'var(--color-text-muted)' }}>Scanned Path</dt>
                  <dd style={{ fontFamily: 'monospace', fontSize: '12px', wordBreak: 'break-all' }}>{symlinkScanResult.scanned_path}</dd>
                  <dt style={{ color: 'var(--color-text-muted)' }}>Total Plugins</dt>
                  <dd>{symlinkScanResult.total_plugins}</dd>
                  <dt style={{ color: 'var(--color-text-muted)' }}>Symlinked</dt>
                  <dd><span className={`badge ${symlinkScanResult.has_symlinks ? 'badge-warning' : 'badge-success'}`}>{symlinkScanResult.symlinked_plugins.length}</span></dd>
                  <dt style={{ color: 'var(--color-text-muted)' }}>Broken</dt>
                  <dd><span className={`badge ${symlinkScanResult.has_broken ? 'badge-error' : 'badge-success'}`}>{symlinkScanResult.broken_symlinks.length}</span></dd>
                </dl>

                {symlinkScanResult.issues.length > 0 && (
                  <div>
                    <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Issues Found</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {symlinkScanResult.issues.map((issue, idx) => (
                        <div key={idx} className="card" style={{ padding: '12px', borderLeft: `4px solid ${issue.issue_type === 'broken' ? 'var(--color-error)' : issue.issue_type === 'symlinked' ? 'var(--color-warning)' : 'var(--color-info)'}` }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                            <strong>{issue.plugin_name}</strong>
                            <span className={`badge ${issue.issue_type === 'broken' ? 'badge-error' : issue.issue_type === 'symlinked' ? 'badge-warning' : 'badge-info'}`}>
                              {issue.issue_type}
                            </span>
                          </div>
                          <p style={{ marginBottom: '8px', color: 'var(--color-text-muted)' }}>{issue.message}</p>
                          {issue.target_path && (
                            <p style={{ fontSize: '12px', fontFamily: 'monospace', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                              Target: {issue.target_path}
                            </p>
                          )}
                          {issue.suggestion && (
                            <p style={{ fontSize: '13px', fontStyle: 'italic', color: 'var(--color-text-muted)' }}>
                              💡 {issue.suggestion}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {symlinkScanResult.issues.length === 0 && symlinkScanResult.total_plugins > 0 && (
                  <div className="alert alert-success">
                    No symlink issues found. All plugins are regular directories.
                  </div>
                )}

                {symlinkScanResult.total_plugins === 0 && (
                  <div className="alert alert-info">
                    No plugins found in the scanned directory.
                  </div>
                )}
              </div>
            )}
          </article>
        </div>
      </section>
    </div>
  );
}
