import { useState } from "react";
import { api } from "../api/client";
import PatientGraph from "../components/PatientGraph";
import PatientJourney from "../components/PatientJourney";
import PatientRisk from "../components/PatientRisk";

export default function Patients() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [journey, setJourney] = useState(null);
  const [subgraph, setSubgraph] = useState(null);
  const [risk, setRisk] = useState(null);
  const [view, setView] = useState("timeline");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch(e) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    try {
      const data = await api.get(`/graph/patients/search?q=${encodeURIComponent(query)}`);
      setResults(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function selectPatient(patient) {
    setSelected(patient);
    setBusy(true);
    setError("");
    try {
      const [journeyData, subgraphData, riskData] = await Promise.all([
        api.get(`/graph/patients/${patient.id}/journey?encounter_limit=10`),
        api.get(`/graph/patients/${patient.id}/subgraph?encounter_limit=10`),
        api.get(`/graph/patients/${patient.id}/risk`),
      ]);
      setJourney(journeyData);
      setSubgraph(subgraphData);
      setRisk(riskData);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="patients-page">
      <div className="patients-sidebar">
        <h3>Find a patient</h3>
        <form onSubmit={handleSearch} className="patient-search-form">
          <input
            type="text"
            placeholder="Search by name..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>

        <div className="patient-results">
          {results.map((p) => (
            <button
              key={p.id}
              className={`patient-result ${selected?.id === p.id ? "selected" : ""}`}
              onClick={() => selectPatient(p)}
            >
              <span className="patient-result-name">
                {p.first_name} {p.last_name}
              </span>
              <span className="patient-result-meta">
                {p.gender} · {p.birthdate}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="patients-main">
        {!selected && (
          <div className="patients-empty">
            Search for a patient by name to see their care journey and
            knowledge-graph subgraph.
          </div>
        )}

        {selected && (
          <>
            <div className="patients-view-toggle">
              <button
                className={view === "timeline" ? "active" : ""}
                onClick={() => setView("timeline")}
              >
                Journey Timeline
              </button>
              <button
                className={view === "graph" ? "active" : ""}
                onClick={() => setView("graph")}
              >
                Graph View
              </button>
              <button
                className={view === "risk" ? "active" : ""}
                onClick={() => setView("risk")}
              >
                Risk
              </button>
            </div>

            {busy && <div className="page-loading">Loading patient data...</div>}
            {error && <div className="form-error">{error}</div>}

            {!busy && view === "timeline" && <PatientJourney journey={journey} />}
            {!busy && view === "graph" && <PatientGraph data={subgraph} />}
            {!busy && view === "risk" && <PatientRisk risk={risk} />}
          </>
        )}
      </div>
    </div>
  );
}
