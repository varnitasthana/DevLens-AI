import type { PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <strong>DevLens</strong>
        <nav className="app-nav">
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/repositories">Repositories</NavLink>
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
