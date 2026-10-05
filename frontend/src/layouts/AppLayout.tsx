import type { PropsWithChildren } from "react";

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <strong>DevLens</strong>
        <span>Developer intelligence, built incrementally.</span>
      </header>
      <main>{children}</main>
    </div>
  );
}
