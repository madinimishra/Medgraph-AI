import { useRef, useState } from "react";
import { api } from "../api/client";

const SAMPLE_QUESTIONS = [
  "How many patients are there in total?",
  "Which 5 hospitals have treated the most patients?",
  "Which two hospitals share the most patients between them?",
  "Which medical conditions most commonly occur together in the same patient?",
  "How many providers have treated patients at more than one hospital?",
];

const ADVANCED_SAMPLE_QUESTIONS = [
  "Compare average healthcare expenses between male and female patients.",
  "Compare the number of emergency encounters for male versus female patients.",
];

function CompareResult({ compare }) {
  if (!compare) return null;

  if (compare.loading) {
    return <div className="compare-panel compare-loading">Running both agents...</div>;
  }

  if (compare.error) {
    return <div className="compare-panel form-error">{compare.error}</div>;
  }

  return (
    <div className="compare-panel">
      <div className="compare-column compare-column-graph">
        <div className="compare-column-title">Graph-only answer</div>
        <p>{compare.graph_answer}</p>
        {compare.graph_cypher && <pre className="compare-cypher">{compare.graph_cypher}</pre>}
      </div>
      <div className="compare-column compare-column-vector">
        <div className="compare-column-title">Vector-only answer (documents only, no graph)</div>
        <p>{compare.vector_answer}</p>
      </div>
    </div>
  );
}

function Inspector({ message, onCompare }) {
  const [open, setOpen] = useState(false);

  const hasGraph = message.cypher || message.graph_error;
  const hasDocs = message.document_matches && message.document_matches.length > 0;
  const hasSubquestions = message.subquestions && message.subquestions.length > 0;

  if (!hasGraph && !hasDocs && !hasSubquestions) return null;

  return (
    <div className="inspector">
      <div className="inspector-buttons">
        <button className="inspector-toggle" onClick={() => setOpen(!open)}>
          {open ? "Hide" : "Show"} how this was answered
        </button>
        <button className="inspector-toggle" onClick={onCompare}>
          Compare with vector-only
        </button>
      </div>

      {open && (
        <div className="inspector-body">
          {hasSubquestions && (
            <div className="inspector-section">
              <h4>Decomposed into {message.subquestions.length} sub-questions</h4>
              {message.sub_results?.map((sr, i) => (
                <div className="subquestion-block" key={i}>
                  <div className="subquestion-text">{sr.subquestion}</div>
                  {sr.cypher && <pre>{sr.cypher}</pre>}
                  {sr.error && <p className="inspector-error">{sr.error}</p>}
                </div>
              ))}
            </div>
          )}

          {message.cypher && (
            <div className="inspector-section">
              <h4>Cypher query generated</h4>
              <pre>{message.cypher}</pre>
            </div>
          )}

          {message.graph_error && (
            <div className="inspector-section">
              <h4>Graph query issue</h4>
              <p className="inspector-error">{message.graph_error}</p>
            </div>
          )}

          {message.graph_results && message.graph_results.length > 0 && (
            <div className="inspector-section">
              <h4>Graph results ({message.graph_results.length})</h4>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      {Object.keys(message.graph_results[0]).map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {message.graph_results.slice(0, 15).map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((val, j) => (
                          <td key={j}>{String(val)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {hasDocs && (
            <div className="inspector-section">
              <h4>Matching uploaded documents ({message.document_matches.length})</h4>
              {message.document_matches.map((doc, i) => (
                <div className="doc-match" key={i}>
                  <div className="doc-match-meta">
                    {doc.metadata?.filename || "document"} · distance{" "}
                    {doc.distance?.toFixed(3)}
                  </div>
                  <div className="doc-match-text">{doc.text}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <CompareResult compare={message.compare} />
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  const scrollRef = useRef(null);

  function scrollToBottom() {
    setTimeout(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }, 50);
  }

  async function send(question) {
    if (!question.trim() || busy) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setBusy(true);

    try {
      const result = await api.post("/chat/ask", { question, advanced });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          question,
          text: result.answer,
          cypher: result.cypher,
          graph_results: result.graph_results,
          graph_error: result.graph_error,
          document_matches: result.document_matches,
          subquestions: result.subquestions,
          sub_results: result.sub_results,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message}`, isError: true },
      ]);
    } finally {
      setBusy(false);
      scrollToBottom();
    }
  }

  async function handleCompare(index) {
    const message = messages[index];
    if (!message?.question) return;

    setMessages((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], compare: { loading: true } };
      return next;
    });
    scrollToBottom();

    try {
      const result = await api.post("/chat/compare", { question: message.question });
      setMessages((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], compare: { ...result, loading: false } };
        return next;
      });
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], compare: { error: err.message } };
        return next;
      });
    }
    scrollToBottom();
  }

  function handleSubmit(e) {
    e.preventDefault();
    send(input);
  }

  const sampleQuestions = advanced ? ADVANCED_SAMPLE_QUESTIONS : SAMPLE_QUESTIONS;

  return (
    <div className="chat-page">
      <div className="chat-sidebar">
        <h3>Try a question</h3>
        <p className="chat-sidebar-hint">
          The assistant combines the hospital knowledge graph with semantic
          search over uploaded documents.
        </p>

        <label className="advanced-toggle">
          <input
            type="checkbox"
            checked={advanced}
            onChange={(e) => setAdvanced(e.target.checked)}
          />
          Advanced multi-step reasoning
        </label>
        <p className="chat-sidebar-hint advanced-hint">
          Decomposes comparisons into sub-questions (LangGraph), answers each
          against the graph, then synthesizes one combined answer.
        </p>

        {sampleQuestions.map((q) => (
          <button
            key={q}
            className="sample-question"
            onClick={() => send(q)}
            disabled={busy}
          >
            {q}
          </button>
        ))}
      </div>

      <div className="chat-main">
        <div className="chat-messages" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="chat-empty">
              Ask anything about patients, hospitals, conditions, medications,
              or uploaded documents.
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`bubble bubble-${m.role}`}>
              <div className="bubble-role">
                {m.role === "user" ? "You" : "MedGraph AI"}
              </div>
              <div className={`bubble-text ${m.isError ? "bubble-error" : ""}`}>
                {m.text}
              </div>
              {m.role === "assistant" && !m.isError && (
                <Inspector message={m} onCompare={() => handleCompare(i)} />
              )}
            </div>
          ))}

          {busy && (
            <div className="bubble bubble-assistant">
              <div className="bubble-role">MedGraph AI</div>
              <div className="bubble-text typing">Thinking...</div>
            </div>
          )}
        </div>

        <form className="chat-input-row" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Ask a question about your hospital data..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={busy}
          />
          <button type="submit" disabled={busy || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
