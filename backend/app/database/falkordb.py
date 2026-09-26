from falkordb import FalkorDB
from app.core.config import settings

db = FalkorDB(
    host=settings.FALKOR_HOST,
    port=settings.FALKOR_PORT
)

graph = db.select_graph(settings.FALKOR_GRAPH)