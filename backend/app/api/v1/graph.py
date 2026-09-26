from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.graph.graph_builder import HospitalGraphBuilder
from app.graph.falkor_client import FalkorGraph
from app.graph import queries as graph_queries
from app.graph import risk_scoring
from app.core.rbac import require_roles
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/graph",
    tags=["Knowledge Graph"]
)


@router.post("/build")
def build_graph(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    HospitalGraphBuilder().build_graph(db)

    return {
        "message": "Knowledge Graph built successfully."
    }


@router.get("/stats")
def graph_stats(
    current_user=Depends(get_current_user)
):
    """Live, schema-agnostic summary of the Synthea knowledge graph -
    labels/relationship types are discovered from FalkorDB itself,
    never hardcoded."""

    graph = FalkorGraph(graph_name=settings.FALKOR_SYNTHEA_GRAPH)

    labels = [
        row[0]
        for row in graph.query("CALL db.labels()").result_set
    ]

    node_counts = {
        label: graph.query(
            f"MATCH (n:{label}) RETURN count(n)"
        ).result_set[0][0]
        for label in labels
    }

    relationship_types = [
        row[0]
        for row in graph.query("CALL db.relationshipTypes()").result_set
    ]

    relationship_counts = {
        rel_type: graph.query(
            f"MATCH ()-[r:{rel_type}]->() RETURN count(r)"
        ).result_set[0][0]
        for rel_type in relationship_types
    }

    return {
        "graph_name": settings.FALKOR_SYNTHEA_GRAPH,
        "node_counts": node_counts,
        "relationship_counts": relationship_counts,
        "total_nodes": sum(node_counts.values()),
        "total_relationships": sum(relationship_counts.values()),
    }


@router.get("/patients/search")
def search_patients(
    q: str,
    limit: int = 20,
    current_user=Depends(get_current_user)
):
    """Search Synthea patients by name, for the patient explorer UI -
    avoids the frontend needing to know raw graph UUIDs up front."""

    if not q or len(q.strip()) < 2:
        return []

    return graph_queries.search_patients(q.strip(), limit=limit)


@router.get("/providers/search")
def search_providers(
    q: str,
    limit: int = 20
):
    """Search Synthea providers by name - intentionally public (no auth)
    since a doctor needs this to find and link their provider_id at
    registration time, before they have an account/token yet."""

    if not q or len(q.strip()) < 2:
        return []

    return graph_queries.search_providers(q.strip(), limit=limit)


@router.get("/patients/{patient_id}/journey")
def patient_journey(
    patient_id: str,
    encounter_limit: int = 15,
    current_user=Depends(get_current_user)
):
    """Chronological encounter timeline for one patient, with the
    conditions/procedures/medications/observations/allergies recorded
    during each encounter."""

    journey = graph_queries.get_patient_journey(patient_id, encounter_limit=encounter_limit)

    if journey is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return journey


@router.get("/patients/{patient_id}/subgraph")
def patient_subgraph(
    patient_id: str,
    encounter_limit: int = 10,
    current_user=Depends(get_current_user)
):
    """Node-link subgraph for one patient's most recent encounters, for
    the graph visualization view."""

    subgraph = graph_queries.get_patient_subgraph(patient_id, encounter_limit=encounter_limit)

    if subgraph is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return subgraph


@router.get("/patients/{patient_id}/risk")
def patient_risk(
    patient_id: str,
    current_user=Depends(get_current_user)
):
    """Transparent, rule-based risk score derived from graph features
    (polypharmacy, emergency-visit history, condition burden, age) -
    see risk_scoring.py for the honesty note on what this is and isn't."""

    risk = risk_scoring.get_patient_risk(patient_id)

    if risk is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return risk