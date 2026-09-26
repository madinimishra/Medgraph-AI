from redis import Redis
from falkordb import FalkorDB

from app.core.config import settings

redis_conn = Redis(
    host=settings.FALKOR_HOST,
    port=settings.FALKOR_PORT,
    decode_responses=True
)

graph = FalkorDB(
    redis_conn,
    settings.FALKOR_GRAPH
)