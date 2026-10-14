/** Home page - public landing page. */
import { useAuth } from '@/hooks/useAuth';
import { NavLink } from 'react-router-dom';

export function HomePage() {
  const { user } = useAuth();

  const workflows = [
    {
      title: 'Plugin Manifest Validator',
      description: 'Validate plugin.json against schema, check SKILL.md frontmatter, verify agents/skills/hooks/mcp.json paths exist, and detect unlisted plugin directories.',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      ),
    },
    {
      title: 'Diff Quality Analyzer',
      description: 'Detect import-filtering-before-numbering and whitespace-collapsing bugs in PR review renderers (Cursor plugins issue #472).',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      ),
    },
    {
      title: 'OAuth Scope Auditor',
      description: 'Audit declared OAuth scopes vs required API scopes for connectors (e.g., Gmail missing gmail.settings.basic per issue #385).',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <rect x="2" y="3" width="20" height="14" rx="2" />
          <path d="M8 21h8" />
          <path d="M12 17v4" />
        </svg>
      ),
    },
  ];

  return (
    <div className="app">
      <header className="header" role="banner">
        <div className="header-brand">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
          <span>Axiom Pilot</span>
        </div>
        <nav className="header-nav" role="navigation" aria-label="Main navigation">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
            Home
          </NavLink>
          {user && (
            <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>
              Dashboard
            </NavLink>
          )}
        </nav>
        <div className="header-user">
          {user ? (
            <div className="user-menu">
              <span>{user.name}</span>
              <span className="badge badge-info">{user.roles.join(', ')}</span>
            </div>
          ) : (
            <NavLink to="/login" className="btn btn-primary">
              Get Started
            </NavLink>
          )}
        </div>
      </header>

      <main className="main">
        <section style={{ textAlign: 'center', padding: '60px 24px', maxWidth: '800px', margin: '0 auto' }}>
          <h1 className="page-title" style={{ fontSize: '48px', marginBottom: '24px' }}>
            AI/ML Developer Tool for Cursor Plugin Quality
          </h1>
          <p className="page-subtitle" style={{ fontSize: '20px', maxWidth: '600px', margin: '0 auto 48px' }}>
            Analyze, validate, and improve Cursor plugins with automated quality checks.
            Built for AI/ML engineers who build developer tools.
          </p>
          {user ? (
            <NavLink to="/dashboard" className="btn btn-primary" style={{ padding: '14px 32px', fontSize: '16px' }}>
              Open Dashboard
            </NavLink>
          ) : (
            <NavLink to="/login" className="btn btn-primary" style={{ padding: '14px 32px', fontSize: '16px' }}>
              Sign In to Start
            </NavLink>
          )}
        </section>

        <section style={{ padding: '0 24px', maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '32px', textAlign: 'center' }}>
            Core Capabilities
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            {workflows.map((w, i) => (
              <article key={i} className="card" style={{ display: 'flex', flexDirection: 'column' }}>
                <div style={{ width: '48px', height: '48px', color: 'var(--color-primary)', marginBottom: '16px' }}>
                  {w.icon}
                </div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px', color: 'var(--color-text)' }}>
                  {w.title}
                </h3>
                <p style={{ color: 'var(--color-text-muted)', lineHeight: '1.6', flex: 1 }}>
                  {w.description}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section style={{ padding: '60px 24px', maxWidth: '1200px', margin: '0 auto', background: 'var(--color-primary-light)', borderRadius: 'var(--radius-lg)', marginTop: '48px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '16px', textAlign: 'center', color: 'var(--color-primary)' }}>
            AI/ML Evaluation Focus
          </h2>
          <p style={{ textAlign: 'center', color: 'var(--color-text-muted)', maxWidth: '700px', margin: '0 auto' }}>
            This tool addresses real AI/ML developer workflows: validating plugin manifests that define agent behaviors,
            analyzing diff rendering quality for code review agents, and auditing OAuth scopes for MCP server connectors.
            Each capability has a deterministic offline core with optional LLM-powered explanations.
          </p>
        </section>
      </main>

      <footer className="footer" role="contentinfo">
        <p>
          Axiom Pilot &copy; 2025 Ryan Vo {" "}<a href="mailto:ryandtvo@gmail.com">ryandtvo@gmail.com</a>
          {' | '}
          <a href="https://github.com/A220man/axiom-pilot-ryan-vo" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
          {' | '}
          <a href="/api/docs" target="_blank" rel="noopener noreferrer">
            API Docs
          </a>
        </p>
      </footer>
    </div>
  );
}