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


class Doctor(Base):

    __tablename__ = "doctors"

    # -------------------------
    # Relationships
    # -------------------------

    department = relationship(
        "Department",
        back_populates="doctors"
    )

    appointments = relationship(
        "Appointment",
        back_populates="doctor"
    )

    medical_records = relationship(
        "MedicalRecord",
        back_populates="doctor"
    )

    # -------------------------
    # Columns
    # -------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    doctor_code = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    full_name = Column(
        String(150),
        nullable=False
    )

    specialization = Column(
        String(100),
        nullable=False
    )

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False
    )

    qualification = Column(
        String(150),
        nullable=False
    )

    experience = Column(
        Integer,
        nullable=False
    )

    phone = Column(
        String(15),
        unique=True,
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )