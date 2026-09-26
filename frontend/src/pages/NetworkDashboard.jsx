import { useEffect, useState } from "react";
import { api } from "../api/client";
import SankeyChart from "../components/SankeyChart";
import ComorbidityHeatmap from "../components/ComorbidityHeatmap";

export default function NetworkDashboard() {
  const [communities, setCommunities] = useState(null);
  const [centrality, setCentrality] = useState(null);
  const [flow, setFlow] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/network/communities"),
      api.get("/network/centrality"),
      api.get("/network/patient-flow"),
      api.get("/network/comorbidity-heatmap"),
    ])
      .then(([c, cent, f, h]) => {
        setCommunities(c);
        setCentrality(cent);
        setFlow(f);
        setHeatmap(h);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Analyzing the network...</div>;
  if (error) return <div className="page form-error">{error}</div>;

  const maxPagerank = Math.max(...(centrality || []).map((c) => c.pagerank), 0.0001);

  return (
    <div className="page network-dashboard">
      <h2>Network Intelligence</h2>
      <p className="page-hint">
        Real graph-theory analysis of the hospital network - not just
        pattern-matching queries. Community detection and centrality run
        actual algorithms (greedy modularity, PageRank, betweenness) on the
        shared-patient network across all facilities.
      </p>

      <div className="network-grid">
        <section className="network-card">
          <h3>Most influential hospitals (PageRank)</h3>
          <p className="network-card-hint">
            Ranked by overall network influence - a hospital connected to
            other well-connected hospitals ranks higher than one with the
            same raw connection count but weaker neighbors.
          </p>
          <div className="bar-list">
            {(centrality || []).slice(0, 10).map((c) => (
              <div className="bar-row" key={c.hospital}>
                <span className="bar-label" title={c.hospital}>
                  {c.hospital}
                </span>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ width: `${(c.pagerank / maxPagerank) * 100}%` }}
                  />
                </div>
                <span className="bar-value">{c.pagerank}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="network-card">
          <h3>Hospital communities</h3>
          <p className="network-card-hint">
            Clusters of facilities that share patients with each other more
            densely than with the rest of the network - found via greedy
            modularity maximization, not manually grouped.
          </p>
          <div className="community-list">
            {(communities || []).slice(0, 6).map((c) => (
              <div className="community-item" key={c.community_id}>
                <div className="community-header">
                  <span>Community {c.community_id + 1}</span>
                  <span className="community-size">{c.size} facilities</span>
                </div>
                <div className="community-hospitals">
                  {c.hospitals.slice(0, 6).join(", ")}
                  {c.hospitals.length > 6 ? `, +${c.hospitals.length - 6} more` : ""}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="network-card network-card-wide">
        <h3>Patient flow between hospitals</h3>
        <p className="network-card-hint">
          Directional: which hospital a patient went to NEXT, in
          chronological order - not just "these two hospitals share
          patients," but which way the flow actually goes.
        </p>
        <SankeyChart data={flow} />
      </section>

      <section className="network-card network-card-wide">
        <h3>Comorbidity heatmap</h3>
        <p className="network-card-hint">
          Co-occurrence of the most common clinical conditions across the
          whole patient population - the diagonal is how many patients
          have that condition at all.
        </p>
        <ComorbidityHeatmap data={heatmap} />
      </section>
    </div>
  );
}
