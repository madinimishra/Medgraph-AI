from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_email = Column(String(150), nullable=False, index=True)
    user_role = Column(String(50), nullable=False)

    question = Column(Text, nullable=False)
    cypher = Column(Text, nullable=True)

    success = Column(Boolean, nullable=False, default=True)
    error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
