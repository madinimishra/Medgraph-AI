import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const ROLES = ["admin", "doctor", "receptionist"];

function ProviderLinkEditor({ user, onSaved }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function search() {
    if (query.trim().length < 2) return;
    setError("");
    try {
      const data = await api.get(`/graph/providers/search?q=${encodeURIComponent(query)}`);
      setResults(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function link(providerId) {
    setBusy(true);
    setError("");
    try {
      const updated = await api.patch(
        `/auth/users/${user.id}/provider`,
        { provider_id: providerId }
      );
      onSaved(updated);
      setResults([]);
      setQuery("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function unlink() {
    setBusy(true);
    setError("");
    try {
      const updated = await api.patch(`/auth/users/${user.id}/provider`, { provider_id: null });
      onSaved(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (user.provider_id) {
    return (
      <div className="admin-provider-editor">
        <span className="deidentified-badge">{user.provider_name || user.provider_id}</span>
        <button className="document-action-btn" disabled={busy} onClick={unlink}>
          Unlink
        </button>
        {error && <div className="form-error">{error}</div>}
      </div>
    );
  }

  return (
    <div className="admin-provider-editor">
      <input
        type="text"
        placeholder="Search provider..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button type="button" className="document-action-btn" onClick={search}>
        Search
      </button>
      {results.length > 0 && (
        <div className="provider-results">
          {results.slice(0, 5).map((p) => (
            <button
              type="button"
              key={p.id}
              className="provider-result"
              disabled={busy}
              onClick={() => link(p.id)}
            >
              <span>{p.name}</span>
              <span className="provider-result-speciality">{p.speciality}</span>
            </button>
          ))}
        </div>
      )}
      {error && <div className="form-error">{error}</div>}
    </div>
  );
}

function RoleEditor({ user, isSelf, onSaved }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function changeRole(e) {
    const role = e.target.value;
    if (role === user.role) return;
    setBusy(true);
    setError("");
    try {
      const updated = await api.patch(`/auth/users/${user.id}/role`, { role });
      onSaved(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (isSelf) {
    return <span className="role-pill">{user.role} (you)</span>;
  }

  return (
    <div>
      <select value={user.role} onChange={changeRole} disabled={busy}>
        {ROLES.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      {error && <div className="form-error">{error}</div>}
    </div>
  );
}

function UsersPanel() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await api.get("/auth/users");
      setUsers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function handleSaved(updated) {
    setUsers((prev) => prev.map((u) => (u.id === updated.id ? { ...u, ...updated } : u)));
  }

  async function handleDelete(u) {
    if (!window.confirm(`Delete ${u.full_name} (${u.email})? This can't be undone.`)) return;
    try {
      await api.del(`/auth/users/${u.id}`);
      setUsers((prev) => prev.filter((x) => x.id !== u.id));
    } catch (err) {
      window.alert(err.message);
    }
  }

  return (
    <section className="admin-section">
      <h2>User management</h2>
      <p className="page-hint">
        Change a role, link/unlink a doctor to a provider record in the graph
        (this is what scopes their chat access to only their own patients),
        or remove an account entirely.
      </p>

      {loading && <div className="page-loading">Loading...</div>}
      {error && <div className="form-error">{error}</div>}

      {!loading && !error && (
        <div className="table-scroll">
          <table className="admin-users-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Provider link</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>
                    <RoleEditor user={u} isSelf={u.id === me?.id} onSaved={handleSaved} />
                  </td>
                  <td>
                    {u.role === "doctor" ? (
                      <ProviderLinkEditor user={u} onSaved={handleSaved} />
                    ) : (
                      <span className="page-hint">n/a</span>
                    )}
                  </td>
                  <td>
                    {u.id !== me?.id && (
                      <button className="document-action-btn danger" onClick={() => handleDelete(u)}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function HealthPanel() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await api.get("/admin/health");
      setHealth(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const rows = health
    ? [
        ["Postgres", health.postgres],
        ["FalkorDB", health.falkordb],
        ["Vector store (Chroma)", health.chroma],
      ]
    : [];

  return (
    <section className="admin-section">
      <h2>System health</h2>
      <p className="page-hint">
        Live connectivity check against every store the app depends on.
      </p>
      <button className="document-action-btn" onClick={load} disabled={loading}>
        {loading ? "Checking..." : "Refresh"}
      </button>
      {error && <div className="form-error">{error}</div>}
      {health && (
        <div className="admin-health-grid">
          {rows.map(([label, info]) => (
            <div className="admin-health-card" key={label}>
              <div className="admin-health-label">{label}</div>
              <div className={`admin-health-status ${info.status === "ok" ? "ok" : "error"}`}>
                {info.status === "ok" ? "Connected" : "Error"}
              </div>
              {info.status === "ok" && info.node_count !== undefined && (
                <div className="page-hint">{info.node_count.toLocaleString()} nodes</div>
              )}
              {info.status === "ok" && info.chunk_count !== undefined && (
                <div className="page-hint">{info.chunk_count.toLocaleString()} chunks</div>
              )}
              {info.status === "error" && <div className="page-hint">{info.detail}</div>}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function DocumentsPanel() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/documents/")
      .then(setDocuments)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="admin-section">
      <h2>Uploaded documents</h2>
      <p className="page-hint">
        Every document uploaded so far, across all users.
      </p>
      {loading && <div className="page-loading">Loading...</div>}
      {error && <div className="form-error">{error}</div>}
      {!loading && !error && (
        <div className="table-scroll">
          <table className="admin-users-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Patient</th>
                <th>Hospital</th>
                <th>Uploaded</th>
                <th>De-identified</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((d) => (
                <tr key={d.document_id}>
                  <td>{d.filename}</td>
                  <td>{d.patient || "-"}</td>
                  <td>{d.hospital || "-"}</td>
                  <td>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleString() : "-"}</td>
                  <td>{d.deidentified ? "Yes" : "No"}</td>
                </tr>
              ))}
              {documents.length === 0 && (
                <tr>
                  <td colSpan={5} className="page-hint">
                    No documents uploaded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function SystemToolsPanel() {
  const [fhirBusy, setFhirBusy] = useState(false);
  const [fhirResult, setFhirResult] = useState(null);
  const [fhirError, setFhirError] = useState("");

  const [buildBusy, setBuildBusy] = useState(false);
  const [buildResult, setBuildResult] = useState("");
  const [buildError, setBuildError] = useState("");

  async function handleFhirUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFhirBusy(true);
    setFhirError("");
    setFhirResult(null);
    try {
      const data = await api.postFile("/fhir/import", file);
      setFhirResult(data);
    } catch (err) {
      setFhirError(err.message);
    } finally {
      setFhirBusy(false);
      e.target.value = "";
    }
  }

  async function handleRebuild() {
    setBuildBusy(true);
    setBuildError("");
    setBuildResult("");
    try {
      const data = await api.post("/graph/build", {});
      setBuildResult(data.message);
    } catch (err) {
      setBuildError(err.message);
    } finally {
      setBuildBusy(false);
    }
  }

  return (
    <section className="admin-section">
      <h2>System tools</h2>

      <div className="admin-tool-block">
        <h3>Import a FHIR R4 bundle</h3>
        <p className="page-hint">
          Upload a FHIR Bundle JSON file (Patient/Encounter/Condition/etc) to
          import it into the graph, same schema as the Synthea dataset.
        </p>
        <input type="file" accept=".json" onChange={handleFhirUpload} disabled={fhirBusy} />
        {fhirBusy && <p className="page-hint">Importing...</p>}
        {fhirError && <div className="form-error">{fhirError}</div>}
        {fhirResult && (
          <pre className="admin-json-result">{JSON.stringify(fhirResult.imported, null, 2)}</pre>
        )}
      </div>

      <div className="admin-tool-block">
        <h3>Rebuild the hospital-CRUD graph</h3>
        <p className="page-hint">
          Resyncs the graph from the Postgres Hospital/Department/Doctor/Patient
          CRUD tables (a separate, smaller graph from the main Synthea dataset).
        </p>
        <button className="document-action-btn" onClick={handleRebuild} disabled={buildBusy}>
          {buildBusy ? "Rebuilding..." : "Rebuild now"}
        </button>
        {buildError && <div className="form-error">{buildError}</div>}
        {buildResult && <div className="form-success">{buildResult}</div>}
      </div>
    </section>
  );
}

export default function Admin() {
  return (
    <div className="page admin-page">
      <h1>Admin</h1>
      <HealthPanel />
      <UsersPanel />
      <DocumentsPanel />
      <SystemToolsPanel />
    </div>
  );
}
