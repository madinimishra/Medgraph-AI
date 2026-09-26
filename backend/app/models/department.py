from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Department(Base):

    __tablename__ = "departments"

    # -------------------------
    # Relationships
    # -------------------------

    hospital = relationship(
        "Hospital",
        back_populates="departments"
    )

    doctors = relationship(
        "Doctor",
        back_populates="department"
    )

    # -------------------------
    # Columns
    # -------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    department_code = Column(
        String(20),
        unique=True,
        nullable=False
    )

    department_name = Column(
        String(100),
        unique=True,
        nullable=False
    )

    description = Column(
        String(300),
        nullable=True
    )

    floor = Column(
        String(50),
        nullable=False
    )

    hod_name = Column(
        String(150),
        nullable=False
    )

    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )