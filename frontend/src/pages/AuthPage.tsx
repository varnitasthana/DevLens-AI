import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { authenticate } from "../services/api";

export function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await authenticate(`/api/v1/auth/${mode}`, email, password);
      navigate("/", { replace: true });
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Authentication failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="detail-card auth-card">
      <p className="eyebrow">Account</p>
      <h2>{mode === "login" ? "Sign in to DevLens" : "Create a DevLens account"}</h2>
      <form className="repository-form" onSubmit={submit}>
        <label>
          Email
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required />
        </label>
        {error && <p className="status status-error">{error}</p>}
        <button disabled={pending}>{pending ? "Submitting…" : mode === "login" ? "Sign in" : "Register"}</button>
      </form>
      <button className="button-muted" onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "Create an account" : "Use an existing account"}
      </button>
    </section>
  );
}
