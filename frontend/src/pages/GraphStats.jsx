import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function GraphStats() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/graph/stats")
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page">Loading graph stats...</div>;
  if (error) return <div className="page form-error">{error}</div>;
  if (!stats) return null;

  const maxNodeCount = Math.max(...Object.values(stats.node_counts), 1);
  const maxRelCount = Math.max(...Object.values(stats.relationship_counts), 1);

  return (
    <div className="page">
      <h2>Knowledge graph: {stats.graph_name}</h2>
      <p className="page-hint">
        Live counts pulled directly from FalkorDB - node labels and
        relationship types are discovered dynamically, not hardcoded.
      </p>

      <div className="stat-summary">
        <div className="stat-box">
          <span className="stat-number">{stats.total_nodes.toLocaleString()}</span>
          <span className="stat-label">total nodes</span>
        </div>
        <div className="stat-box">
          <span className="stat-number">
            {stats.total_relationships.toLocaleString()}
          </span>
          <span className="stat-label">total relationships</span>
        </div>
      </div>

      <h3>Nodes by label</h3>
      <div className="bar-list">
        {Object.entries(stats.node_counts)
          .sort((a, b) => b[1] - a[1])
          .map(([label, count]) => (
            <div className="bar-row" key={label}>
              <span className="bar-label">{label}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${(count / maxNodeCount) * 100}%` }}
                />
              </div>
              <span className="bar-value">{count.toLocaleString()}</span>
            </div>
          ))}
      </div>

      <h3>Relationships by type</h3>
      <div className="bar-list">
        {Object.entries(stats.relationship_counts)
          .sort((a, b) => b[1] - a[1])
          .map(([label, count]) => (
            <div className="bar-row" key={label}>
              <span className="bar-label">{label}</span>
              <div className="bar-track">
                <div
                  className="bar-fill bar-fill-rel"
                  style={{ width: `${(count / maxRelCount) * 100}%` }}
                />
              </div>
              <span className="bar-value">{count.toLocaleString()}</span>
            </div>
          ))}
      </div>
    </div>
  );
}
