import json
import re

from app.core.llm_client import generate_content
from app.graph.falkor_client import FalkorGraph
from app.core.config import settings

GRAPH_SCHEMA = """
Node labels and properties:

(:Patient {id, first_name, last_name, birthdate, deathdate, gender, race,
           ethnicity, birthplace, address, city, state, county, zip,
           latitude, longitude, healthcare_expenses, healthcare_coverage})

(:Organization {id, name, address, city, state, zip, latitude, longitude,
                 phone, revenue, utilization})
    -- Organization is a hospital / healthcare facility.

(:Provider {id, name, gender, speciality, address, city, state, zip,
            latitude, longitude, utilization})

(:Encounter {id, start_time, stop_time, encounter_class, code, description,
             base_encounter_cost, total_claim_cost, payer_coverage,
             reason_code, reason_description})
    -- encounter_class is one of: wellness, ambulatory, urgentcare,
       emergency, outpatient, inpatient.

(:Condition {id, start_date, end_date, code, description})
(:Procedure {id, start_time, stop_time, code, description, base_cost,
             reason_code, reason_description})
(:Medication {id, start_time, stop_time, code, description, base_cost,
              payer_coverage, dispenses, total_cost,
              reason_code, reason_description})
(:Observation {id, observation_date, category, code, description, value,
               units, type})
(:Allergy {id, start_date, stop_date, code, system, description,
           allergy_type, category, reaction1, description1, severity1,
           reaction2, description2, severity2})

Relationships:

(:Patient)-[:HAD_ENCOUNTER]->(:Encounter)
(:Encounter)-[:PROVIDED_BY]->(:Provider)
(:Encounter)-[:AT]->(:Organization)
(:Provider)-[:WORKS_AT]->(:Organization)
    -- In this dataset every Provider's Encounters are all AT their one
       home organization - providers do NOT cross hospitals. Patients DO:
       most patients (~98%) have encounters at 2+ different Organizations.
       Cross-hospital network patterns come from shared PATIENTS across
       Organizations, not from shared providers.
(:Patient)-[:HAS_CONDITION]->(:Condition)
(:Encounter)-[:HAS_CONDITION]->(:Condition)
(:Patient)-[:UNDERWENT]->(:Procedure)
(:Procedure)-[:DURING]->(:Encounter)
(:Patient)-[:TAKES]->(:Medication)
(:Medication)-[:DURING]->(:Encounter)
(:Patient)-[:HAS_OBSERVATION]->(:Observation)
(:Encounter)-[:HAS_OBSERVATION]->(:Observation)
(:Patient)-[:HAS_ALLERGY]->(:Allergy)
(:Encounter)-[:HAS_ALLERGY]->(:Allergy)

Notes:
- "Hospital" in user questions refers to an (:Organization) node, matched
  by Organization.name (case-insensitive, may need CONTAINS matching).
- All id properties are strings.
- Dates/timestamps are stored as strings (ISO-like), sortable as text.
- There is no explicit "referral" relationship in this data. A question
  about "referrals" or "which hospitals send patients to which" must be
  answered by INFERRING network structure from shared entities (e.g. a
  provider who has encounters at more than one organization, or patients
  who see providers at multiple organizations) - not by looking for a
  REFERS_TO edge, which does not exist.
"""

MULTI_HOP_EXAMPLES = """
Example multi-hop / network-pattern questions and the Cypher that answers
them. Use these as a guide for structuring similar relationship-level
questions - do not just copy them if the question is different.

Q: "Which conditions most commonly occur together in the same patient?"
   (comorbidity clustering - filter to '(disorder)' descriptions to avoid
   social/administrative "finding" codes like stress or employment status;
   normalize pair order so A+B and B+A are counted together; dedupe a
   patient's conditions with collect(DISTINCT ...) first since the same
   condition can repeat across many encounters)
MATCH (p:Patient)-[:HAS_CONDITION]->(c:Condition)
WHERE c.description CONTAINS '(disorder)'
WITH p, collect(DISTINCT c.description) AS conditions
UNWIND range(0, size(conditions)-2) AS i
UNWIND range(i+1, size(conditions)-1) AS j
WITH CASE WHEN conditions[i] < conditions[j] THEN conditions[i] ELSE conditions[j] END AS condition_a,
     CASE WHEN conditions[i] < conditions[j] THEN conditions[j] ELSE conditions[i] END AS condition_b
RETURN condition_a, condition_b, count(*) AS patient_count
ORDER BY patient_count DESC
LIMIT 25

Q: "Which two hospitals share the most patients between them?" /
   "Which hospitals are most connected in the network?"
MATCH (p:Patient)-[:HAD_ENCOUNTER]->(:Encounter)-[:AT]->(o1:Organization)
MATCH (p)-[:HAD_ENCOUNTER]->(:Encounter)-[:AT]->(o2:Organization)
WHERE o1.id < o2.id
RETURN o1.name AS hospital_a, o2.name AS hospital_b,
       count(DISTINCT p) AS shared_patients
ORDER BY shared_patients DESC
LIMIT 25

Q: "Which patients have received care at the most hospitals?"
   (patient cross-hospital mobility - this is the real "network" signal in
   this dataset: providers stay at one hospital, but ~98% of patients are
   seen at 2+ different hospitals)
MATCH (p:Patient)-[:HAD_ENCOUNTER]->(:Encounter)-[:AT]->(o:Organization)
WITH p, count(DISTINCT o) AS hospital_count
WHERE hospital_count > 1
RETURN p.first_name AS first_name, p.last_name AS last_name, hospital_count
ORDER BY hospital_count DESC
LIMIT 25

Q: "Find two patients connected through a shared provider."
MATCH (p1:Patient)-[:HAD_ENCOUNTER]->(:Encounter)-[:PROVIDED_BY]->(pr:Provider),
      (pr)<-[:PROVIDED_BY]-(:Encounter)<-[:HAD_ENCOUNTER]-(p2:Patient)
WHERE p1.id < p2.id
RETURN p1.first_name AS patient_a, p2.first_name AS patient_b,
       pr.name AS shared_provider
LIMIT 25

Note on shortestPath: FalkorDB only supports DIRECTED shortestPath (no
mixed-direction/undirected variable-length patterns), so only use it for
single relationship-type, single-direction chains you are confident exist
in this schema - do not use it for cross-entity network paths.
"""

WRITE_KEYWORDS = re.compile(
    r"\b(MERGE|CREATE|SET|DELETE|REMOVE|DROP|CALL\s+db\.|"
    r"CALL\s+dbms\.|FOREACH)\b",
    re.IGNORECASE
)

MAX_ATTEMPTS = 3


class GraphRAGAgent:
    """Text-to-Cypher agent that answers natural language questions
    about the Synthea hospital knowledge graph in FalkorDB. Includes
    self-correction: if a generated query fails validation or execution,
    the error is fed back to the model for up to MAX_ATTEMPTS retries.

    Optionally accepts a `scope` dict ({"role": ..., "provider_id": ...})
    to enforce RBAC: a "doctor" scope requires the generated query to be
    restricted to that provider's own patients. This is enforced
    programmatically (not just requested in the prompt) via
    is_scoped_to_provider, reusing the same retry-with-feedback loop used
    for syntax errors - a query that doesn't scope correctly is rejected
    and regenerated, the same as a query that fails to execute."""

    def __init__(self):
        self.graph = FalkorGraph(graph_name=settings.FALKOR_SYNTHEA_GRAPH)

    # -------------------------
    # Step 1: NL question -> Cypher
    # -------------------------
    def generate_cypher(
        self,
        question: str,
        error_context: str = None,
        scope: dict = None
    ) -> str:

        correction_block = ""
        if error_context:
            correction_block = f"""
Your previous attempt failed with this error:
{error_context}

Fix the query so it no longer produces this error. Double-check node
labels, relationship names/directions, and property names against the
schema exactly.
"""

        scope_block = ""
        if scope and scope.get("role") == "doctor" and scope.get("provider_id"):
            provider_id = scope["provider_id"]
            scope_block = f"""
ACCESS CONTROL (mandatory, non-negotiable):
This request comes from a doctor account, restricted to their own
patients only. If the query returns or traverses through ANY (:Patient)
node, you MUST constrain it to patients connected to
(:Provider {{id: '{provider_id}'}}) via a
(p:Patient)-[:HAD_ENCOUNTER]->(:Encounter)-[:PROVIDED_BY]->(:Provider {{id: '{provider_id}'}})
path. Add this as an explicit MATCH/WHERE constraint in your query - do
not answer with patients outside this provider's care. If the question
has nothing to do with patients (e.g. it's about hospitals or providers
in general), you do not need this constraint.
"""

        prompt = f"""
You are an expert at writing Cypher queries for FalkorDB.

Graph schema:
{GRAPH_SCHEMA}

{MULTI_HOP_EXAMPLES}

Rules:
- Write ONE read-only Cypher query that answers the question.
- Prefer relationship/network-level patterns (multi-hop traversals,
  aggregation across shared nodes) when the question asks about patterns,
  connections, overlap, or "in common" - not just a single lookup.
- Only use MATCH, WHERE, RETURN, WITH, ORDER BY, LIMIT, UNWIND, OPTIONAL MATCH,
  COUNT, shortestPath, and other read/aggregation clauses.
- NEVER use MERGE, CREATE, SET, DELETE, REMOVE, or DROP.
- Always include a LIMIT (default 25) unless the question asks for a single
  aggregate value (e.g. a count or average).
- For ANY question about which "conditions"/"diseases"/"diagnoses" occur
  together (comorbidity): you MUST filter to c.description CONTAINS
  '(disorder)' (excludes social/administrative "finding" codes like
  employment status or stress, which are not diseases), you MUST dedupe
  each patient's conditions with collect(DISTINCT c.description) before
  pairing them (the same condition repeats across many encounters), and
  you MUST normalize the pair order (e.g. with a CASE WHEN a < b ...)
  so that A-paired-with-B and B-paired-with-A are not counted separately.
  Follow the comorbidity example under MULTI_HOP_EXAMPLES exactly for
  this query shape.
- Return ONLY valid JSON in this exact format, no markdown fences:
  {{"cypher": "<the cypher query>"}}
{scope_block}
{correction_block}
Question:
{question}
"""

        output = generate_content(prompt, purpose="cypher_generation")

        if output.startswith("```"):
            output = output.strip("`")
            if output.startswith("json"):
                output = output[4:]
            output = output.strip()

        try:
            parsed = json.loads(output)
            return parsed["cypher"].strip()
        except (json.JSONDecodeError, KeyError, TypeError):
            raise ValueError(
                f"Model did not return valid Cypher JSON: {output}"
            )

    # -------------------------
    # Step 2: Safety checks
    # -------------------------
    @staticmethod
    def is_read_only(cypher: str) -> bool:
        return WRITE_KEYWORDS.search(cypher) is None

    @staticmethod
    def is_scoped_to_provider(cypher: str, provider_id: str) -> bool:
        """Proxy check that the doctor-scoping constraint is actually
        present in the generated query. Not a substitute for real
        row-level security (FalkorDB has none), but it does verify the
        query textually references the caller's own provider_id rather
        than silently ignoring the access-control instruction - and if
        it doesn't, the query is rejected and regenerated rather than
        executed."""

        if not re.search(r"\bPatient\b", cypher):
            # Query doesn't touch patients at all - nothing to scope.
            return True

        return provider_id in cypher

    # -------------------------
    # Step 3: Execute against FalkorDB
    # -------------------------
    def run_query(self, cypher: str):

        result = self.graph.query(cypher)

        header = [col[1] for col in result.header] if result.header else []

        rows = [
            dict(zip(header, row))
            for row in result.result_set
        ]

        return header, rows

    # -------------------------
    # Step 3b: Generate + validate + execute, with self-correction
    # -------------------------
    def generate_and_run(self, question: str, scope: dict = None):

        error_context = None
        last_error = None
        cypher = None

        requires_scoping = bool(
            scope and scope.get("role") == "doctor" and scope.get("provider_id")
        )

        for attempt in range(MAX_ATTEMPTS):

            cypher = self.generate_cypher(question, error_context=error_context, scope=scope)

            if not self.is_read_only(cypher):
                last_error = "Generated query was blocked: not read-only."
                error_context = last_error
                continue

            if requires_scoping and not self.is_scoped_to_provider(cypher, scope["provider_id"]):
                last_error = (
                    "Generated query touches Patient data but does not include the "
                    f"required access-control constraint restricting results to "
                    f"Provider {{id: '{scope['provider_id']}'}}'s own patients. "
                    "Add the MATCH/WHERE constraint described in the ACCESS CONTROL "
                    "section."
                )
                error_context = last_error
                continue

            try:
                header, rows = self.run_query(cypher)
                return cypher, header, rows, attempt + 1
            except Exception as e:
                last_error = str(e)
                error_context = last_error

        raise ValueError(
            f"Cypher generation failed after {MAX_ATTEMPTS} attempts. "
            f"Last error: {last_error}. Last query tried: {cypher}"
        )

    # -------------------------
    # Step 4: Synthesize NL answer from results
    # -------------------------
    def synthesize_answer(self, question: str, rows: list) -> str:

        preview = json.dumps(rows[:25], default=str, ensure_ascii=False)

        prompt = f"""
You are a helpful medical data assistant. Answer the user's question using
ONLY the query results below. Be concise and factual. If the results list
is completely empty (no rows at all), say no matching data was found.

IMPORTANT: a numeric value of 0 (e.g. a count, total, or average of 0) IS
a real, complete answer - state it confidently (e.g. "0 providers match
this"). Do NOT treat a returned 0 value as if no data was found - only
say "no data found" when there are zero rows, never because a value
happens to be 0 or false.

Question: {question}

Query results (JSON, possibly truncated): {preview}

Answer:
"""

        return generate_content(prompt, purpose="answer_synthesis")

    # -------------------------
    # Full pipeline
    # -------------------------
    def ask(self, question: str, scope: dict = None) -> dict:

        cypher, header, rows, attempts = self.generate_and_run(question, scope=scope)

        answer = self.synthesize_answer(question, rows)

        return {
            "question": question,
            "cypher": cypher,
            "columns": header,
            "results": rows,
            "answer": answer,
            "attempts": attempts,
        }
