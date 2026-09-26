from falkordb import FalkorDB


HOST = "localhost"
PORT = 6379
GRAPH_NAME = "medgraph_synthea"


def main():
    print("[INFO] Connecting to FalkorDB...")

    db = FalkorDB(
        host=HOST,
        port=PORT
    )

    graph = db.select_graph(GRAPH_NAME)

    result = graph.query(
        "RETURN 1 AS connected"
    )

    print("[SUCCESS] FalkorDB connected!")
    print("[INFO] Graph:", GRAPH_NAME)
    print("[INFO] Result:", result.result_set)


if __name__ == "__main__":
    main()