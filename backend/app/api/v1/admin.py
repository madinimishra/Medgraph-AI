from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.rbac import require_roles
from app.database.session import get_db
from app.core.config import settings
from app.graph.falkor_client import FalkorGraph
from app.vectorstore.chroma_manager import get_collection

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/health")
def system_health(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    """Live connectivity + size check for every store the app depends
    on - lets an admin see at a glance whether the whole stack is up,
    without needing shell access to check each service separately."""

    health = {}

    try:
        db.execute(text("SELECT 1"))
        health["postgres"] = {"status": "ok"}
    except Exception as e:
        health["postgres"] = {"status": "error", "detail": str(e)}

    try:
        graph = FalkorGraph(graph_name=settings.FALKOR_SYNTHEA_GRAPH)
        result = graph.query("MATCH (n) RETURN count(n) AS count")
        node_count = result.result_set[0][0]
        health["falkordb"] = {"status": "ok", "graph": settings.FALKOR_SYNTHEA_GRAPH, "node_count": node_count}
    except Exception as e:
        health["falkordb"] = {"status": "error", "detail": str(e)}

    try:
        collection = get_collection()
        health["chroma"] = {"status": "ok", "chunk_count": collection.count()}
    except Exception as e:
        health["chroma"] = {"status": "error", "detail": str(e)}

    return health
