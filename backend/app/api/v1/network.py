from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.graph import network_analysis, network_viz

router = APIRouter(
    prefix="/network",
    tags=["Network Analysis"]
)


@router.get("/communities")
def communities(current_user=Depends(get_current_user)):
    """Hospital/facility communities found via greedy modularity
    maximization on the shared-patient network - real community
    detection, not a hand-picked grouping."""

    return network_analysis.get_hospital_communities()


@router.get("/centrality")
def centrality(top_n: int = 15, current_user=Depends(get_current_user)):
    """Degree/betweenness/PageRank centrality of each hospital in the
    shared-patient network."""

    return network_analysis.get_hospital_centrality(top_n=top_n)


@router.get("/patient-flow")
def patient_flow(top_n: int = 20, current_user=Depends(get_current_user)):
    """Directed patient-flow transitions between hospitals, for a
    Sankey diagram."""

    return network_viz.get_patient_flow(top_n=top_n)


@router.get("/comorbidity-heatmap")
def comorbidity_heatmap(top_n: int = 12, current_user=Depends(get_current_user)):
    """Condition x condition co-occurrence matrix over the most common
    real clinical disorders, for a heatmap."""

    return network_viz.get_comorbidity_heatmap(top_n_conditions=top_n)
