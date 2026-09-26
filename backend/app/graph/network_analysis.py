"""Real graph-theory analysis of the hospital network - community
detection and centrality - as opposed to the pattern-matching Cypher
queries used elsewhere. This is deliberately built on networkx rather
than hand-rolled: community detection and centrality are well-studied
algorithms, and networkx's implementations are the standard, correct
ones to reach for rather than reinventing them.

The network modeled here is Organizations (hospitals) connected by
shared patients - this is the real cross-hospital "network" signal in
this dataset (see ARCHITECTURE.md: providers don't cross hospitals,
~98% of patients do), so it's the graph worth running these algorithms
on.
"""

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from app.graph.queries import get_synthea_graph


def _build_hospital_overlap_graph() -> nx.Graph:
    """An undirected, weighted graph: one node per hospital, one edge
    per pair of hospitals that share at least one patient, weighted by
    how many patients they share."""

    graph = get_synthea_graph()

    result = graph.query(
        """
        MATCH (p:Patient)-[:HAD_ENCOUNTER]->(:Encounter)-[:AT]->(o1:Organization)
        MATCH (p)-[:HAD_ENCOUNTER]->(:Encounter)-[:AT]->(o2:Organization)
        WHERE o1.id < o2.id
        RETURN o1.name AS hospital_a, o2.name AS hospital_b,
               count(DISTINCT p) AS shared_patients
        """
    )

    header = [col[1] for col in result.header]
    rows = [dict(zip(header, row)) for row in result.result_set]

    G = nx.Graph()
    for row in rows:
        G.add_edge(
            row["hospital_a"],
            row["hospital_b"],
            weight=row["shared_patients"]
        )

    return G


def get_hospital_communities(min_community_size: int = 2) -> list[dict]:
    """Clusters hospitals into communities using greedy modularity
    maximization (Clauset-Newman-Moore) on the shared-patient network.
    A "community" here is a group of hospitals that are more densely
    connected to each other (via shared patients) than to the rest of
    the network - i.e. a natural sub-network, not an arbitrary grouping.
    """

    G = _build_hospital_overlap_graph()

    if G.number_of_nodes() == 0:
        return []

    communities = list(greedy_modularity_communities(G, weight="weight"))

    results = []
    for index, community in enumerate(communities):
        hospitals = sorted(community)
        if len(hospitals) < min_community_size:
            continue

        # Internal cohesion: total shared-patient weight of edges that
        # stay within this community, vs. edges leaving it.
        subgraph = G.subgraph(hospitals)
        internal_weight = sum(
            data["weight"] for _, _, data in subgraph.edges(data=True)
        )

        results.append({
            "community_id": index,
            "hospitals": hospitals,
            "size": len(hospitals),
            "internal_shared_patients": internal_weight,
        })

    results.sort(key=lambda c: c["size"], reverse=True)
    return results


def get_hospital_centrality(top_n: int = 15) -> list[dict]:
    """Three complementary centrality measures on the same network:

    - degree_centrality: how many OTHER hospitals this one shares
      patients with, directly - a simple "how connected" measure.
    - betweenness_centrality: how often this hospital sits on the
      shortest path between two other hospitals - identifies "bridge"
      hospitals connecting otherwise-separate parts of the network.
    - pagerank: overall influence, weighted by how connected ITS
      neighbors are too, not just raw connection count - the same
      algorithm that ranks web pages, applied to hospital connectivity.
    """

    G = _build_hospital_overlap_graph()

    if G.number_of_nodes() == 0:
        return []

    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, weight="weight")
    pagerank = nx.pagerank(G, weight="weight")

    results = [
        {
            "hospital": hospital,
            "degree_centrality": round(degree.get(hospital, 0), 4),
            "betweenness_centrality": round(betweenness.get(hospital, 0), 4),
            "pagerank": round(pagerank.get(hospital, 0), 4),
        }
        for hospital in G.nodes()
    ]

    results.sort(key=lambda r: r["pagerank"], reverse=True)
    return results[:top_n]
