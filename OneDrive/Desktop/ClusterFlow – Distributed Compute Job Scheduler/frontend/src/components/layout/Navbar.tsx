import * as React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useWebSocket } from '../../context/WebSocketContext';
import { Button } from '../ui/Button';
import { Logo } from '../ui/Logo';

export const Navbar: React.FC = () => {
  const { isConnected } = useWebSocket();
  const location = useLocation();
  const navigate = navigateFn();
  const userJson = localStorage.getItem('cf_user');
  const user = userJson ? JSON.parse(userJson) : null;

  function navigateFn() {
    try {
      return useNavigate();
    } catch {
      return () => {};
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('cf_token');
    localStorage.removeItem('cf_user');
    window.dispatchEvent(new Event('auth_logout'));
    navigate('/login');
  };

  const isActive = (path: string) => {
    return location.pathname === path 
      ? 'text-foreground font-semibold' 
      : 'text-muted-foreground hover:text-foreground transition-colors';
  };

  if (!user) return null;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-none items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Logo className="h-5 w-5" /> ClusterFlow
          </Link>

          <nav className="hidden lg:flex items-center gap-6 text-sm font-medium">
            <Link to="/" className={isActive('/')}>Dashboard</Link>
            <Link to="/jobs" className={isActive('/jobs')}>Jobs</Link>
            <Link to="/workers" className={isActive('/workers')}>Workers</Link>
            <Link to="/scheduler" className={isActive('/scheduler')}>Queues</Link>
            <Link to="/telemetry" className={isActive('/telemetry')}>Metrics</Link>
            <Link to="/cluster" className={isActive('/cluster')}>Cluster</Link>
            <Link to="/settings" className={isActive('/settings')}>Settings</Link>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {/* Real-time Connection Indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary border border-border text-xs font-medium">
            <span className="relative flex h-2 w-2">
              {isConnected && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isConnected ? 'bg-emerald-500' : 'bg-destructive'}`}></span>
            </span>
            <span className="text-muted-foreground hidden sm:inline">{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground bg-secondary px-3 py-1.5 border border-border rounded-md font-medium">
              {user.email} ({user.role})
            </span>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};
