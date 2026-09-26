from fastapi import APIRouter, Depends

from app.core.rbac import require_roles
from app.core import observability

router = APIRouter(
    prefix="/observability",
    tags=["Observability"]
)


@router.get("/stats")
def get_observability_stats(
    current_user=Depends(require_roles("admin"))
):
    """Aggregated LLM call latency/token/fallback stats for this running
    process - admin-only, since it can reveal usage patterns."""

    return observability.get_stats()
