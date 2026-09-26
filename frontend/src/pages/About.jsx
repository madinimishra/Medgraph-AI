import { Link } from "react-router-dom";
import Logo from "../components/Logo";

const STATS = [
  ["779K+", "graph nodes, real hospital-network scale"],
  ["3", "roles with enforced, fail-closed access control"],
  ["100%", "answers traceable to a query or source document"],
];

const USERS = [
  ["🏥 Hospital administrators", "Understand patient flow, referral-like patterns, and network-wide trends"],
  ["👨‍⚕️ Doctors", "Look up a patient's full journey - scoped to only their own patients"],
  ["🔬 Researchers / analysts", "Find disease patterns, comorbidities, and cross-hospital relationships"],
  ["🏢 Network management", "See which hospitals are most central, and how the network clusters"],
  ["💻 Healthcare IT teams", "Query complex hospital data in plain English instead of manual queries"],
  ["🧑‍💼 Compliance / admin staff", "Use the audit log to see who accessed what data, and when"],
];

const FEATURES = [
  "Ask any question about the hospital network in plain English",
  "Every answer traced back to its exact graph query or source document",
  "Automatically decomposes complex, comparative questions into sub-questions",
  "Combines graph search with semantic search over uploaded documents",
  "Real graph algorithms - community detection and centrality, not just lookups",
  "A doctor's access is programmatically restricted to their own patients",
  "Imports real-world FHIR healthcare data, not just synthetic test data",
  "Transparent, non-clinical risk flagging - never a black-box diagnosis",
  "A full audit trail of who asked what, and when",
];

export default function About() {
  return (
    <div className="about-page">
      <div className="about-hero">
        <div className="about-hero-brandrow">
          <Logo size={48} />
          <div className="auth-hero-brand">MedGraph AI</div>
        </div>
        <h1 className="auth-hero-tagline">See the network behind the data.</h1>
        <p className="about-hero-sub">
          Hybrid GraphRAG for multi-hospital networks - ask a question in
          plain English, get an answer traced back to the exact graph query
          or document behind it.
        </p>
        <div className="about-stats">
          {STATS.map(([value, label]) => (
            <div className="about-stat" key={label}>
              <div className="about-stat-value">{value}</div>
              <div className="about-stat-label">{label}</div>
            </div>
          ))}
        </div>
      </div>

      <section className="about-section">
        <h2>The problem</h2>
        <p>
          Hospital networks generate patient data across many hospitals,
          providers, and record types. Conventional databases handle
          single-record lookups well, but struggle with questions that span{" "}
          <em>relationships</em> across many entities — multi-hop joins that
          don't scale in SQL. Plain text-search AI has no notion of
          structured relationships or aggregation at all.
        </p>
        <p>
          <strong>MedGraph AI</strong> builds a knowledge graph across the
          network and answers relationship-level questions through natural
          language — combined with semantic search over unstructured
          clinical documents — in one hybrid, source-traceable interface.
        </p>
      </section>

      <section className="about-section">
        <h2>What it can do</h2>
        <ul className="about-feature-list">
          {FEATURES.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </section>

      <section className="about-section">
        <h2>Who it's for</h2>
        <p className="page-hint">
          A B2B healthcare intelligence platform for multi-hospital
          networks — not a patient-facing app, and not a replacement for
          clinical judgement.
        </p>
        <div className="about-users-grid">
          {USERS.map(([title, desc]) => (
            <div className="about-user-card" key={title}>
              <div className="about-user-title">{title}</div>
              <div className="about-user-desc">{desc}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="about-section about-cta">
        <Link to="/login" className="about-cta-btn">
          Sign in
        </Link>
        <Link to="/register" className="switch-link">
          or create an account
        </Link>
      </section>
    </div>
  );
}
