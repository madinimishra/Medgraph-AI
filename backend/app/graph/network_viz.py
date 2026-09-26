"""Network-wide visualization data: patient flow between hospitals
(for a Sankey diagram) and comorbidity co-occurrence (for a heatmap).
Both are computed from the full Synthea graph, not a sample - see
falkor_client.py for why that matters (FalkorDB's default 10K result
cap would otherwise silently bias these towards whichever patients
happened to sort first)."""

from collections import defaultdict

import networkx as nx

from app.graph.queries import get_synthea_graph


def get_patient_flow(top_n: int = 20) -> dict:
    """Directed hospital-to-hospital patient flow: for each patient,
    walk their encounters in chronological order and count a "flow"
    every time they move from one organization to a different one.
    This is a genuinely directional, temporal signal - different from
    the undirected "shared patients" count used elsewhere."""

    graph = get_synthea_graph()

    result = graph.query(
        """
        MATCH (p:Patient)-[:HAD_ENCOUNTER]->(e:Encounter)-[:AT]->(o:Organization)
        RETURN p.id AS patient_id, e.start_time AS start_time, o.name AS hospital
        ORDER BY p.id, e.start_time
        """
    )

    header = [col[1] for col in result.header]
    rows = [dict(zip(header, row)) for row in result.result_set]

    transitions = defaultdict(int)
    current_patient = None
    last_hospital = None

    for row in rows:
        if row["patient_id"] != current_patient:
            current_patient = row["patient_id"]
            last_hospital = row["hospital"]
            continue

        if row["hospital"] != last_hospital:
            transitions[(last_hospital, row["hospital"])] += 1
            last_hospital = row["hospital"]

    # Real patient flow is naturally bidirectional (some patients go
    # A->B, others go B->A) - a Sankey layout requires an acyclic graph,
    # so each unordered pair is collapsed to its NET direction (the
    # difference), not just the larger raw count, before picking the
    # top N. Any longer cycle (A->B->C->A) that could still slip through
    # is then broken by dropping its weakest edge, using networkx to
    # detect it rather than assuming pairwise collapsing was enough.
    net_transitions = {}
    seen_pairs = set()

    for (a, b), count in transitions.items():
        pair_key = frozenset((a, b))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        reverse_count = transitions.get((b, a), 0)
        net = count - reverse_count

        if net > 0:
            net_transitions[(a, b)] = net
        elif net < 0:
            net_transitions[(b, a)] = -net
        # net == 0: equal flow both ways, genuinely no net direction - drop.

    top_transitions = sorted(
        net_transitions.items(), key=lambda item: item[1], reverse=True
    )[:top_n]

    # Break any remaining longer cycles: keep removing the globally
    # weakest edge of a detected cycle until the graph is a DAG.
    dag = nx.DiGraph()
    for (source, target), value in top_transitions:
        dag.add_edge(source, target, weight=value)

    while True:
        try:
            cycle = nx.find_cycle(dag)
        except nx.NetworkXNoCycle:
            break
        weakest = min(cycle, key=lambda edge: dag.edges[edge[0], edge[1]]["weight"])
        dag.remove_edge(*weakest[:2])

    nodes = []
    node_index = {}

    def get_node_index(name):
        if name not in node_index:
            node_index[name] = len(nodes)
            nodes.append(name)
        return node_index[name]

    links = [
        {
            "source": get_node_index(source),
            "target": get_node_index(target),
            "value": data["weight"],
        }
        for source, target, data in dag.edges(data=True)
    ]

    return {"nodes": nodes, "links": links}


def get_comorbidity_heatmap(top_n_conditions: int = 12) -> dict:
    """A condition x condition co-occurrence matrix restricted to the
    N most common real clinical disorders, for a heatmap - the general
    text-to-Cypher agent can already answer "which conditions occur
    together" one pair at a time, but a full matrix over the most
    common conditions is a genuinely different, network-wide view."""

    graph = get_synthea_graph()

    top_result = graph.query(
        """
        MATCH (c:Condition)
        WHERE c.description CONTAINS '(disorder)'
        RETURN c.description AS description, count(*) AS n
        ORDER BY n DESC
        LIMIT $limit
        """,
        {"limit": top_n_conditions}
    )
    top_conditions = [row[0] for row in top_result.result_set]

    if not top_conditions:
        return {"conditions": [], "matrix": []}

    pair_result = graph.query(
        """
        MATCH (p:Patient)-[:HAS_CONDITION]->(c:Condition)
        WHERE c.description IN $conditions
        WITH p, collect(DISTINCT c.description) AS conditions
        UNWIND range(0, size(conditions)-1) AS i
        UNWIND range(0, size(conditions)-1) AS j
        WITH conditions[i] AS condition_a, conditions[j] AS condition_b
        RETURN condition_a, condition_b, count(*) AS patient_count
        """,
        {"conditions": top_conditions}
    )

    header = [col[1] for col in pair_result.header]
    rows = [dict(zip(header, row)) for row in pair_result.result_set]

    counts = {(r["condition_a"], r["condition_b"]): r["patient_count"] for r in rows}

    matrix = [
        [counts.get((row_condition, col_condition), 0) for col_condition in top_conditions]
        for row_condition in top_conditions
    ]

    return {"conditions": top_conditions, "matrix": matrix}
