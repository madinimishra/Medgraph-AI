from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditService:

    @staticmethod
    def log(
        db: Session,
        user_email: str,
        user_role: str,
        question: str,
        cypher: str = None,
        success: bool = True,
        error: str = None,
    ):
        entry = AuditLog(
            user_email=user_email,
            user_role=user_role,
            question=question,
            cypher=cypher,
            success=success,
            error=error,
        )
        db.add(entry)
        db.commit()

    @staticmethod
    def list_recent(db: Session, limit: int = 100):
        return (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
