from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.rbac import require_roles
from app.services.audit_service import AuditService
from app.schemas.audit import AuditLogEntry

router = APIRouter(
    prefix="/audit",
    tags=["Audit"]
)


@router.get("/logs", response_model=list[AuditLogEntry])
def list_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    """Every chat question asked, by whom, and whether it succeeded -
    admin-only. This is what every question in this system's chat has
    been logged for, since the RBAC work: not just gating access, but
    being able to show who asked what."""

    return AuditService.list_recent(db, limit=limit)
