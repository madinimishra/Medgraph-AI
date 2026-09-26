# Path to production

This project is a working prototype proving a real approach — hybrid
GraphRAG over a hospital network's data — on synthetic data (Synthea)
plus a demonstrated FHIR import path. It is **not** a system ready to
touch real patient data. This document is deliberately explicit about
that line: what's already real, what's been proven feasible but isn't
"real" yet, and what would need dedicated work before this could run
against an actual hospital's data.

## Already real, not just a demo

- **The data model and retrieval logic don't depend on synthetic data.**
  The graph schema, the text-to-Cypher agent, RBAC scoping, and every
  query pattern operate on the schema, not on Synthea specifically.
- **FHIR ingestion is real, not aspirational.** `app/ingestion/fhir_importer.py`
  parses actual FHIR R4 Bundles (the standard real EHR systems export)
  and maps them onto the same graph schema - proven end-to-end: a
  FHIR-imported patient is immediately queryable through the same chat
  agent as every Synthea patient, with zero special-casing. See
  `data/sample_fhir_bundle.json` and `tests/test_fhir_importer.py`.
- **De-identification is implemented, not just described.**
  `app/ingestion/deidentification.py` masks HIPAA Safe Harbor-style
  direct identifiers (names, dates, phone, email, SSN) before text
  enters the vector search index - tested in `tests/test_deidentification.py`.
- **A local/self-hosted LLM path exists**, so the architecture doesn't
  structurally require sending data to a public API (see
  [Compliance](#compliance--data-handling) below).

## What's still a prototype, and specifically why

### Data integration
Real hospitals don't hand over a clean CSV or a single FHIR bundle -
integration means talking to a live EHR system (Epic, Cerner, etc.)
via their actual APIs, handling incremental updates (not one-time
loads), reconciling duplicate/conflicting records across systems, and
handling FHIR's full spec surface (this importer handles the common
field shapes, not every legal variation). This is a systems-integration
project on its own, not a weekend addition.

### Compliance & data handling
- No real patient data should touch this system without a signed
  **Business Associate Agreement (BAA)** with every vendor in the data
  path (LLM provider, cloud host, etc.) - Google's public Gemini API,
  as configured here by default, has no such agreement.
- De-identification here is regex/pattern-based, not a clinically
  validated NLP de-identification system - real deployments use
  purpose-built tools (e.g. Philter, AWS Comprehend Medical) and still
  don't claim 100% recall on adversarial or unusual input.
- Data at rest needs encryption (Postgres/FalkorDB here run without it),
  and the audit log would need to be tamper-evident, not just a table
  any admin can query.
- A local LLM (see below) removes the "data leaves the building" risk
  entirely for the AI layer, but the rest of the stack (Postgres,
  FalkorDB, file storage) still needs the same encryption/access
  controls any healthcare system requires regardless of the AI question.

### Model reliability & safety
- LLM hallucination is a materially bigger risk in healthcare than
  elsewhere - a wrong answer about a medication interaction is
  dangerous, not just embarrassing. The self-correction and RBAC
  scoping here reduce *some* failure modes, but a real clinical tool
  needs human-in-the-loop review before any answer informs care, plus
  much more adversarial testing than this project's 22-question
  benchmark.
- The risk-scoring feature (`app/graph/risk_scoring.py`) is explicitly
  a transparent heuristic, not a validated predictive model - Synthea
  has no real outcome labels to train or validate against. A real
  clinical risk score needs a labeled outcomes dataset, a proper
  train/validation/test methodology, and in the US, likely FDA review
  as clinical decision-support software.

### Local LLM option (privacy-preserving, no data leaves the building)

`app/core/llm_client.py` already supports a model fallback chain
(`GEMINI_MODEL` -> `GEMINI_MODEL_FALLBACKS`). The same mechanism
supports pointing at a locally-run model via
[Ollama](https://ollama.com) instead of - or as a fallback to - a
public API, so the architecture doesn't structurally require sending
any data outside the hospital's own infrastructure:

```bash
# run a local model (one-time)
ollama pull llama3.1:8b
ollama serve

# point the app at it instead of / alongside Gemini
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
```

This is materially slower and less capable than Gemini for the
Cypher-generation task specifically (see the model comparison notes
in `ARCHITECTURE.md`), which is *why* it isn't the default - but
proving it's a config change, not an architecture change, is the
point: a real deployment could run entirely on infrastructure the
hospital controls.

## What a real deployment would need, roughly in order

1. A signed BAA and formal data-processing agreement with every vendor
   in the path (or fully self-hosted LLM + infra).
2. Encryption at rest and in transit for every datastore, not just TLS
   on the API.
3. A real EHR integration (FHIR API client against a live system, not
   a one-time bundle upload), including incremental sync.
4. A validated, purpose-built de-identification pipeline, reviewed by
   someone with healthcare privacy expertise - not this regex utility.
5. Clinical validation of the risk-scoring feature against real
   outcomes data, with appropriate regulatory review, before it
   informs any real care decision - or removal of the feature entirely
   if that validation isn't pursued.
6. A much larger, adversarially-designed evaluation set, plus
   human-in-the-loop review for any answer that could affect care.
7. A tamper-evident audit trail and formal access-control review.

None of this is a criticism of the prototype - it's the honest
distance between "proves the idea works" and "safe to run on real
patients," and knowing exactly where that line is is the point of
writing it down.
