from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    id: int
    user_email: str
    user_role: str
    question: str
    cypher: Optional[str] = None
    success: bool
    error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
