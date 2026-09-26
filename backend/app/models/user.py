from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    email = Column(String(150), unique=True, nullable=False, index=True)

    password = Column(String, nullable=False)

    role = Column(String(50), default="admin")

    # Links a "doctor" role user to their Provider node in the Synthea
    # knowledge graph (FalkorDB), so graph chat queries can be scoped to
    # only the patients that provider has actually treated. Nullable -
    # only meaningful for role == "doctor".
    provider_id = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())