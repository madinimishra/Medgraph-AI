import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function AuditLog() {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.role !== "admin") {
      setLoading(false);
      return;
    }
    api
      .get("/audit/logs")
      .then(setLogs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [user]);

  if (user?.role !== "admin") {
    return (
      <div className="page">
        <h2>Audit Log</h2>
        <p className="page-hint">This page is only available to admin accounts.</p>
      </div>
    );
  }

  if (loading) return <div className="page-loading">Loading...</div>;
  if (error) return <div className="page form-error">{error}</div>;

  return (
    <div className="page">
      <h2>Audit Log</h2>
      <p className="page-hint">
        Every question asked through the chat, who asked it, and whether it
        succeeded - the same data every RBAC decision in this system is
        made from, made visible.
      </p>

      <div className="audit-table-scroll">
        <table className="audit-table">
          <thead>
            <tr>
              <th>When</th>
              <th>User</th>
              <th>Role</th>
              <th>Question</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{log.user_email}</td>
                <td>{log.user_role}</td>
                <td className="audit-question-cell">{log.question}</td>
                <td>
                  <span className={`audit-status ${log.success ? "audit-ok" : "audit-fail"}`}>
                    {log.success ? "OK" : "Failed"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {logs.length === 0 && <p className="page-hint">No questions logged yet.</p>}
    </div>
  );
}
