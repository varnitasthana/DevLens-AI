import { useEffect, useState, type PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";
import { clearAuthToken, getAuthToken } from "../services/api";

export function AppLayout({ children }: PropsWithChildren) {
  const [authenticated, setAuthenticated] = useState(() => Boolean(getAuthToken()));

  useEffect(() => {
    const updateAuthentication = () => setAuthenticated(Boolean(getAuthToken()));
    window.addEventListener("devlens-auth-changed", updateAuthentication);
    return () => window.removeEventListener("devlens-auth-changed", updateAuthentication);
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <strong>DevLens</strong>
        <nav className="app-nav">
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/repositories">Repositories</NavLink>
          {authenticated ? (
            <button className="button-muted" onClick={() => { clearAuthToken(); window.location.reload(); }}>Sign out</button>
          ) : (
            <NavLink to="/auth">Sign in</NavLink>
          )}
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
