const LEVEL_COLORS = {
  high: "#ef5b6f",
  moderate: "#f2b544",
  low: "#4cc38a",
};

export default function PatientRisk({ risk }) {
  if (!risk) return null;

  return (
    <div className="patient-risk">
      <div className="risk-summary">
        <div
          className="risk-badge"
          style={{ background: LEVEL_COLORS[risk.risk_level] || "#9aa5c0" }}
        >
          {risk.risk_level.toUpperCase()}
        </div>
        <div>
          <div className="risk-score">Risk score: {risk.risk_score}</div>
          <div className="risk-meta">
            Age {risk.age ?? "unknown"} · {risk.medication_count} medications ·{" "}
            {risk.emergency_encounter_count} emergency visits ·{" "}
            {risk.condition_count} diagnosed conditions
          </div>
        </div>
      </div>

      <h4>Contributing factors</h4>
      {risk.factors.length === 0 ? (
        <p className="page-hint">No risk factors detected.</p>
      ) : (
        <table className="risk-factors-table">
          <thead>
            <tr>
              <th>Factor</th>
              <th>Detail</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            {risk.factors.map((f, i) => (
              <tr key={i}>
                <td>{f.factor.replaceAll("_", " ")}</td>
                <td>{f.detail}</td>
                <td>+{f.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p className="risk-disclaimer">{risk.disclaimer}</p>
    </div>
  );
}
