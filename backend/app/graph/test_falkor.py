from falkordb import FalkorDB


db = FalkorDB(
    host="localhost",
    port=6379
)

graph = db.select_graph("hospital_graph")

result = graph.query("""
    RETURN 1 AS test
""")

print(result.result_set)