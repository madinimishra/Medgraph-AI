"""Reusable read-only Cypher queries against the Synthea knowledge graph,
used by the patient-explorer / visualization API endpoints. Kept separate
from the text-to-Cypher agent - these are hand-written, fixed-shape
queries for known UI needs, not LLM-generated ones.
"""

from app.graph.falkor_client import FalkorGraph
from app.core.config import settings


def get_synthea_graph() -> FalkorGraph:
    return FalkorGraph(graph_name=settings.FALKOR_SYNTHEA_GRAPH)


def _rows_as_dicts(result) -> list[dict]:
    header = [col[1] for col in result.header] if result.header else []
    return [dict(zip(header, row)) for row in result.result_set]


def search_patients(query: str, limit: int = 20) -> list[dict]:

    graph = get_synthea_graph()

    result = graph.query(
        """
        MATCH (p:Patient)
        WHERE toLower(p.first_name + ' ' + p.last_name) CONTAINS toLower($query)
        RETURN p.id AS id, p.first_name AS first_name, p.last_name AS last_name,
               p.gender AS gender, p.birthdate AS birthdate
        LIMIT $limit
        """,
        {"query": query, "limit": limit}
    )

    return _rows_as_dicts(result)


def search_providers(query: str, limit: int = 20) -> list[dict]:

    graph = get_synthea_graph()

    result = graph.query(
        """
        MATCH (pr:Provider)
        WHERE toLower(pr.name) CONTAINS toLower($query)
        RETURN pr.id AS id, pr.name AS name, pr.speciality AS speciality
        LIMIT $limit
        """,
        {"query": query, "limit": limit}
    )

    return _rows_as_dicts(result)


def get_provider(provider_id: str) -> dict:
    """A single provider's name/speciality by id, or None - used to
    show a human-readable name next to a linked provider_id instead of
    a raw UUID (e.g. in the admin user-management panel)."""

    graph = get_synthea_graph()

    result = graph.query(
        "MATCH (pr:Provider {id: $id}) RETURN pr.id AS id, pr.name AS name, pr.speciality AS speciality",
        {"id": provider_id}
    )

    rows = _rows_as_dicts(result)
    return rows[0] if rows else None


def get_patient_journey(patient_id: str, encounter_limit: int = 15) -> dict:
    """Chronological encounters for one patient, each with the
    conditions/procedures/medications/observations/allergies recorded
    during that encounter - the data behind a patient journey timeline."""

    graph = get_synthea_graph()

    patient_result = graph.query(
        """
        MATCH (p:Patient {id: $id})
        RETURN p.id AS id, p.first_name AS first_name, p.last_name AS last_name,
               p.gender AS gender, p.birthdate AS birthdate, p.race AS race,
               p.ethnicity AS ethnicity
        """,
        {"id": patient_id}
    )
    patients = _rows_as_dicts(patient_result)
    if not patients:
        return None
    patient = patients[0]

    encounters_result = graph.query(
        """
        MATCH (p:Patient {id: $id})-[:HAD_ENCOUNTER]->(e:Encounter)
        OPTIONAL MATCH (e)-[:PROVIDED_BY]->(pr:Provider)
        OPTIONAL MATCH (e)-[:AT]->(o:Organization)
        RETURN e.id AS encounter_id, e.start_time AS start_time,
               e.stop_time AS stop_time, e.encounter_class AS encounter_class,
               e.description AS description,
               pr.name AS provider_name, o.name AS organization_name
        ORDER BY e.start_time DESC
        LIMIT $limit
        """,
        {"id": patient_id, "limit": encounter_limit}
    )
    encounters = _rows_as_dicts(encounters_result)
    encounter_ids = [e["encounter_id"] for e in encounters]

    conditions_by_encounter = _group_by_encounter(graph, encounter_ids, "HAS_CONDITION", forward=True)
    observations_by_encounter = _group_by_encounter(graph, encounter_ids, "HAS_OBSERVATION", forward=True)
    allergies_by_encounter = _group_by_encounter(graph, encounter_ids, "HAS_ALLERGY", forward=True)
    procedures_by_encounter = _group_by_encounter(graph, encounter_ids, "DURING", forward=False, label="Procedure")
    medications_by_encounter = _group_by_encounter(graph, encounter_ids, "DURING", forward=False, label="Medication")

    for encounter in encounters:
        eid = encounter["encounter_id"]
        encounter["conditions"] = conditions_by_encounter.get(eid, [])
        encounter["observations"] = observations_by_encounter.get(eid, [])
        encounter["allergies"] = allergies_by_encounter.get(eid, [])
        encounter["procedures"] = procedures_by_encounter.get(eid, [])
        encounter["medications"] = medications_by_encounter.get(eid, [])

    return {"patient": patient, "encounters": encounters}


def _group_by_encounter(
    graph: FalkorGraph,
    encounter_ids: list[str],
    relationship: str,
    forward: bool,
    label: str = None
) -> dict:

    if not encounter_ids:
        return {}

    if forward:
        cypher = f"""
        UNWIND $ids AS eid
        MATCH (e:Encounter {{id: eid}})-[:{relationship}]->(n)
        RETURN eid AS encounter_id, n.id AS id, n.description AS description
        """
    else:
        cypher = f"""
        UNWIND $ids AS eid
        MATCH (n:{label})-[:{relationship}]->(e:Encounter {{id: eid}})
        RETURN eid AS encounter_id, n.id AS id, n.description AS description
        """

    result = graph.query(cypher, {"ids": encounter_ids})
    rows = _rows_as_dicts(result)

    grouped = {}
    for row in rows:
        grouped.setdefault(row["encounter_id"], []).append({
            "id": row["id"],
            "description": row["description"],
        })
    return grouped


def get_patient_subgraph(patient_id: str, encounter_limit: int = 10) -> dict:
    """Node-link subgraph (nodes + edges) for a patient's most recent
    encounters, for visualization. Scoped to encounter_limit encounters
    so the graph stays legible in a UI rather than dumping hundreds of
    historical entries."""

    journey = get_patient_journey(patient_id, encounter_limit=encounter_limit)
    if journey is None:
        return None

    patient = journey["patient"]
    nodes = {}
    edges = []

    patient_node_id = f"patient:{patient['id']}"
    nodes[patient_node_id] = {
        "id": patient_node_id,
        "label": f"{patient['first_name']} {patient['last_name']}",
        "type": "Patient",
    }

    graph = get_synthea_graph()
    encounter_ids = [e["encounter_id"] for e in journey["encounters"]]

    orgs_result = graph.query(
        """
        UNWIND $ids AS eid
        MATCH (e:Encounter {id: eid})-[:AT]->(o:Organization)
        OPTIONAL MATCH (e)-[:PROVIDED_BY]->(pr:Provider)
        RETURN eid AS encounter_id, o.id AS org_id, o.name AS org_name,
               pr.id AS provider_id, pr.name AS provider_name
        """,
        {"ids": encounter_ids}
    ) if encounter_ids else None
    org_provider_rows = _rows_as_dicts(orgs_result) if orgs_result else []
    org_provider_by_encounter = {}
    for row in org_provider_rows:
        org_provider_by_encounter[row["encounter_id"]] = row

    for encounter in journey["encounters"]:
        eid = encounter["encounter_id"]
        enc_node_id = f"encounter:{eid}"

        nodes[enc_node_id] = {
            "id": enc_node_id,
            "label": encounter["description"] or encounter["encounter_class"] or "Encounter",
            "type": "Encounter",
            "start_time": encounter["start_time"],
        }
        edges.append({"source": patient_node_id, "target": enc_node_id, "type": "HAD_ENCOUNTER"})

        info = org_provider_by_encounter.get(eid)
        if info and info.get("org_id"):
            org_node_id = f"organization:{info['org_id']}"
            nodes[org_node_id] = {
                "id": org_node_id, "label": info["org_name"], "type": "Organization"
            }
            edges.append({"source": enc_node_id, "target": org_node_id, "type": "AT"})

        if info and info.get("provider_id"):
            provider_node_id = f"provider:{info['provider_id']}"
            nodes[provider_node_id] = {
                "id": provider_node_id, "label": info["provider_name"], "type": "Provider"
            }
            edges.append({"source": enc_node_id, "target": provider_node_id, "type": "PROVIDED_BY"})

        for condition in encounter["conditions"]:
            cid = f"condition:{condition['id']}"
            nodes[cid] = {"id": cid, "label": condition["description"], "type": "Condition"}
            edges.append({"source": enc_node_id, "target": cid, "type": "HAS_CONDITION"})

        for procedure in encounter["procedures"]:
            pid = f"procedure:{procedure['id']}"
            nodes[pid] = {"id": pid, "label": procedure["description"], "type": "Procedure"}
            edges.append({"source": enc_node_id, "target": pid, "type": "UNDERWENT"})

        for medication in encounter["medications"]:
            mid = f"medication:{medication['id']}"
            nodes[mid] = {"id": mid, "label": medication["description"], "type": "Medication"}
            edges.append({"source": enc_node_id, "target": mid, "type": "TAKES"})

    return {"nodes": list(nodes.values()), "edges": edges}
