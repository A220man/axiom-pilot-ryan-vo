/** Header component with navigation and user menu. */
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
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
            <span className={`badge badge-info`}>{user.roles.join(', ')}</span>
            <button className="btn btn-ghost" onClick={handleLogout} aria-label="Sign out">
              Logout
            </button>
          </div>
        ) : (
          <NavLink to="/login" className="btn btn-primary">
            Sign In
          </NavLink>
        )}
      </div>
    </header>
  );
}