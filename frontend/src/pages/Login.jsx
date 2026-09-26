import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Logo from "../components/Logo";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/chat");
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-hero">
        <div className="auth-hero-brandrow">
          <Logo size={40} />
          <div className="auth-hero-brand">MedGraph AI</div>
        </div>
        <h2 className="auth-hero-tagline">See the network behind the data.</h2>
        <p className="auth-hero-copy">
          A hybrid GraphRAG system for cross-hospital clinical intelligence -
          ask natural-language questions about patients, providers, and
          hospitals, and get answers traced back to the exact graph query or
          document behind them.
        </p>
        <ul className="auth-hero-list">
          <li>779K+ node knowledge graph across a real hospital network</li>
          <li>Community detection &amp; PageRank on the hospital network</li>
          <li>Self-correcting text-to-Cypher agent with role-based access</li>
        </ul>
      </div>

      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>MedGraph AI</h1>
        <p className="subtitle">Sign in to your hospital account</p>

        <label>Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && <div className="form-error">{error}</div>}

        <button type="submit" disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </button>

        <p className="switch-link">
          No account? <Link to="/register">Register</Link>
        </p>
        <p className="switch-link">
          <Link to="/about">Learn more about MedGraph AI</Link>
        </p>
      </form>
    </div>
  );
}
