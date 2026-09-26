import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";

const ROLES = ["admin", "doctor", "receptionist"];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(ROLES[0]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [busy, setBusy] = useState(false);

  const [providerQuery, setProviderQuery] = useState("");
  const [providerResults, setProviderResults] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [providerSearchError, setProviderSearchError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [providerSearchBusy, setProviderSearchBusy] = useState(false);

  async function runProviderSearch(query) {
    setProviderSearchError("");
    setProviderSearchBusy(true);
    try {
      const results = await api.get(
        `/graph/providers/search?q=${encodeURIComponent(query)}`
      );
      setProviderResults(results);
      setHasSearched(true);
    } catch (err) {
      setProviderSearchError(err.message || "Search failed");
    } finally {
      setProviderSearchBusy(false);
    }
  }

  async function handleProviderSearch(e) {
    e.preventDefault();
    if (providerQuery.trim().length < 2) return;
    await runProviderSearch(providerQuery);
  }

  async function handleBrowseSample() {
    // This directory only has Synthea's auto-generated synthetic provider
    // names, not real staff names - "an" matches broadly (the backend
    // requires 2+ characters) so someone who doesn't know the naming
    // convention still has a way to find and pick any provider rather
    // than being stuck guessing a name that matches.
    setProviderQuery("an");
    await runProviderSearch("an");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(fullName, email, password, role, selectedProvider?.id);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      setError(err.message || "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  function handleRoleChange(newRole) {
    setRole(newRole);
    if (newRole !== "doctor") {
      setSelectedProvider(null);
      setProviderResults([]);
      setProviderQuery("");
      setHasSearched(false);
    }
  }

  function handleProviderQueryChange(value) {
    setProviderQuery(value);
    setHasSearched(false);
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>MedGraph AI</h1>
        <p className="subtitle">Create a hospital staff account</p>

        <label>Full name</label>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />

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

        <label>Role</label>
        <select value={role} onChange={(e) => handleRoleChange(e.target.value)}>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        {role === "doctor" && (
          <div className="provider-link-block">
            <label>Link your provider record</label>
            <p className="provider-link-hint">
              Required to use Chat - a doctor account with no linked provider
              is blocked from chat by design (it can't be given unrestricted
              patient access by default). You can skip this and ask an admin
              to link it later, but Chat won't work until then.
            </p>
            <p className="provider-link-hint">
              Note: this directory is the sample dataset's auto-generated
              provider names (e.g. "Isabela97 Báez684"), not real staff -
              your own name likely won't match. Use "Browse sample providers"
              below to pick any one for testing.
            </p>

            {selectedProvider ? (
              <div className="provider-selected">
                <div>
                  <strong>{selectedProvider.name}</strong>
                  <span className="provider-selected-speciality">
                    {selectedProvider.speciality}
                  </span>
                </div>
                <button
                  type="button"
                  className="provider-change-btn"
                  onClick={() => setSelectedProvider(null)}
                >
                  Change
                </button>
              </div>
            ) : (
              <>
                <div className="provider-search-row">
                  <input
                    type="text"
                    placeholder="Search the provider directory..."
                    value={providerQuery}
                    onChange={(e) => handleProviderQueryChange(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={handleProviderSearch}
                    disabled={providerSearchBusy}
                  >
                    Search
                  </button>
                </div>

                <button
                  type="button"
                  className="provider-browse-btn"
                  onClick={handleBrowseSample}
                  disabled={providerSearchBusy}
                >
                  Browse sample providers instead
                </button>

                {providerSearchError && (
                  <div className="form-error">{providerSearchError}</div>
                )}

                {providerSearchBusy && (
                  <p className="page-hint">Searching...</p>
                )}

                {!providerSearchBusy && hasSearched && providerResults.length === 0 && (
                  <p className="form-error">
                    No providers matched "{providerQuery}". Try a shorter or
                    different search, or use "Browse sample providers".
                  </p>
                )}

                {providerResults.length > 0 && (
                  <div className="provider-results">
                    {providerResults.map((p) => (
                      <button
                        type="button"
                        key={p.id}
                        className="provider-result"
                        onClick={() => {
                          setSelectedProvider(p);
                          setProviderResults([]);
                        }}
                      >
                        <span>{p.name}</span>
                        <span className="provider-result-speciality">
                          {p.speciality}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {error && <div className="form-error">{error}</div>}
        {success && (
          <div className="form-success">Account created, redirecting...</div>
        )}

        <button type="submit" disabled={busy}>
          {busy ? "Creating..." : "Create account"}
        </button>

        <p className="switch-link">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
