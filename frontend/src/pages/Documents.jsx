import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Documents() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [documents, setDocuments] = useState([]);
  const [listError, setListError] = useState("");
  const [listLoading, setListLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [deidentify, setDeidentify] = useState(false);
  const [fileActionError, setFileActionError] = useState("");
  const [fileActionBusyId, setFileActionBusyId] = useState(null);
  const [viewer, setViewer] = useState(null);

  async function loadDocuments() {
    setListLoading(true);
    setListError("");
    try {
      const data = await api.get("/documents/");
      setDocuments(data);
    } catch (err) {
      setListError(err.message || "Could not load uploaded documents");
    } finally {
      setListLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;

    setBusy(true);
    setError("");
    setResult(null);

    try {
      const data = await api.postFile("/documents/upload", file, {
        deidentify: deidentify ? "true" : "false",
      });
      setResult(data);
      setFile(null);
      setFileInputKey((k) => k + 1);
      await loadDocuments();
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleView(doc) {
    setFileActionError("");
    setFileActionBusyId(doc.document_id);
    try {
      const blob = await api.getBlob(`/documents/${doc.document_id}/file`);
      const url = URL.createObjectURL(blob);
      setViewer({ url, filename: doc.filename, type: blob.type });
    } catch (err) {
      setFileActionError(err.message || "Could not open this file");
    } finally {
      setFileActionBusyId(null);
    }
  }

  function closeViewer() {
    if (viewer) URL.revokeObjectURL(viewer.url);
    setViewer(null);
  }

  async function handleDownload(doc) {
    setFileActionError("");
    setFileActionBusyId(doc.document_id);
    try {
      const blob = await api.getBlob(`/documents/${doc.document_id}/file`);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = doc.filename || "document";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setFileActionError(err.message || "Could not download this file");
    } finally {
      setFileActionBusyId(null);
    }
  }

  return (
    <div className="page">
      <h2>Upload a hospital document</h2>
      <p className="page-hint">
        PDF, DOCX, TXT, image, CSV, XLSX, or XML. The document is parsed,
        chunked, embedded for semantic search, and its extracted entities are
        merged into the knowledge graph.
      </p>

      <form className="upload-form" onSubmit={handleUpload}>
        <input
          key={fileInputKey}
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <button type="submit" disabled={!file || busy}>
          {busy ? "Processing..." : "Upload & process"}
        </button>
      </form>

      <label className="deidentify-toggle">
        <input
          type="checkbox"
          checked={deidentify}
          onChange={(e) => setDeidentify(e.target.checked)}
        />
        De-identify before storing in the search index (masks names,
        dates, contact info, SSNs - HIPAA Safe Harbor style)
      </label>

      {error && <div className="form-error">{error}</div>}

      {result && (
        <div className="result-card">
          <h3>
            Processed successfully
            {result.deidentified && (
              <span className="deidentified-badge">De-identified</span>
            )}
          </h3>
          <dl>
            <dt>Characters extracted</dt>
            <dd>{result.characters}</dd>
            <dt>Chunks created</dt>
            <dd>{result.total_chunks}</dd>
            <dt>Patient record id</dt>
            <dd>{result.patient_id}</dd>
          </dl>

          <h4>Extracted entities</h4>
          <pre>{JSON.stringify(result.entities, null, 2)}</pre>

          <h4>First chunk preview</h4>
          <p className="preview-text">{result.preview}</p>
        </div>
      )}

      <h2 className="documents-list-heading">Uploaded documents</h2>

      {listLoading && <div className="page-loading">Loading...</div>}
      {listError && <div className="form-error">{listError}</div>}

      {!listLoading && !listError && documents.length === 0 && (
        <p className="page-hint">No documents uploaded yet.</p>
      )}

      {fileActionError && <div className="form-error">{fileActionError}</div>}

      {!listLoading && documents.length > 0 && (
        <div className="documents-list">
          {documents.map((doc) => {
            const isOpen = expanded === doc.document_id;
            const isBusy = fileActionBusyId === doc.document_id;
            return (
              <div className="document-card" key={doc.document_id}>
                <div className="document-card-header">
                  <div
                    className="document-card-toggle-area"
                    onClick={() => setExpanded(isOpen ? null : doc.document_id)}
                  >
                    <span className="document-filename">
                      {doc.filename}
                      {doc.deidentified && (
                        <span className="deidentified-badge">De-identified</span>
                      )}
                    </span>
                    <span className="document-meta">
                      {doc.patient ? `${doc.patient} · ` : ""}
                      {doc.department || "General"} · {doc.doctor || "Unknown doctor"}
                    </span>
                  </div>

                  <div className="document-card-actions">
                    <button
                      className="document-action-btn"
                      disabled={isBusy}
                      onClick={() => handleView(doc)}
                    >
                      View
                    </button>
                    <button
                      className="document-action-btn"
                      disabled={isBusy}
                      onClick={() => handleDownload(doc)}
                    >
                      Download
                    </button>
                    <button
                      className="document-toggle"
                      onClick={() => setExpanded(isOpen ? null : doc.document_id)}
                    >
                      {isOpen ? "−" : "+"}
                    </button>
                  </div>
                </div>

                {isOpen && (
                  <div className="document-card-body">
                    <dl>
                      <dt>Hospital</dt>
                      <dd>{doc.hospital || "—"}</dd>
                      <dt>Uploaded</dt>
                      <dd>{doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString() : "unknown"}</dd>
                    </dl>
                    <p className="preview-text">{doc.preview}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {viewer && (
        <div className="pdf-viewer-overlay" onClick={closeViewer}>
          <div className="pdf-viewer-panel" onClick={(e) => e.stopPropagation()}>
            <div className="pdf-viewer-header">
              <span>{viewer.filename}</span>
              <button className="pdf-viewer-close" onClick={closeViewer}>
                Close ✕
              </button>
            </div>
            {viewer.type.startsWith("application/pdf") ||
            viewer.type.startsWith("image/") ||
            viewer.type.startsWith("text/") ? (
              <iframe
                src={viewer.url}
                title={viewer.filename}
                className="pdf-viewer-frame"
              />
            ) : (
              <div className="pdf-viewer-unsupported">
                This file type can't be previewed inline. Use Download instead.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
