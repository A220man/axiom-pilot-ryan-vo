/** 404 Not Found page. */
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="app">
      <main className="main" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <h3>Page Not Found</h3>
          <p style={{ marginBottom: '24px', maxWidth: '300px' }}>
            The page you're looking for doesn't exist or has been moved.
          </p>
          <Link to="/" className="btn btn-primary">Go Home</Link>
        </div>
      </main>
      <footer className="footer" role="contentinfo">
        <p>
          Axiom Pilot &copy; 2025 Ryan Vo {" "}<a href="mailto:ryandtvo@gmail.com">ryandtvo@gmail.com</a>
          {' | '}
          <a href="https://github.com/A220man/axiom-pilot-ryan-vo" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}