from falkordb import FalkorDB

from app.core.config import settings

_resultset_size_configured = False


def _ensure_unlimited_resultset_size(db: FalkorDB):
    """FalkorDB defaults GRAPH.CONFIG RESULTSET_SIZE to 10,000 - any
    query returning more rows than that is SILENTLY truncated (no
    error, no warning). This is a real, easy-to-miss correctness bug:
    an aggregation over 61K+ encounters would quietly analyze only the
    first 10K unless this is raised. Done once per process, not per
    connection, since it's a server-wide config, not a per-graph one.
    """

    global _resultset_size_configured

    if _resultset_size_configured:
        return

    db.connection.execute_command("GRAPH.CONFIG", "SET", "RESULTSET_SIZE", -1)
    _resultset_size_configured = True


class FalkorGraph:

    def __init__(self, graph_name: str = None):
        self.host = settings.FALKOR_HOST
        self.port = settings.FALKOR_PORT
        self.graph_name = graph_name or settings.FALKOR_GRAPH

        self.db = FalkorDB(
            host=self.host,
            port=self.port
        )

        _ensure_unlimited_resultset_size(self.db)

        self.graph = self.db.select_graph(
            self.graph_name
        )

    def query(self, cypher: str, params=None):

        if params is None:
            params = {}

        return self.graph.query(
            cypher,
            params
        )
