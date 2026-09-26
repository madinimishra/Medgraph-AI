from sqlalchemy import (
    Column,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False
    )

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False
    )

    appointment_id = Column(
        Integer,
        ForeignKey("appointments.id"),
        nullable=False
    )

    diagnosis = Column(
        Text,
        nullable=False
    )

    symptoms = Column(
        Text,
        nullable=True
    )

    prescription = Column(
        Text,
        nullable=True
    )

    lab_tests = Column(
        Text,
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    follow_up_date = Column(
        Date,
        nullable=True
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

    # -------------------------
    # Relationships
    # -------------------------

    patient = relationship(
        "Patient",
        back_populates="medical_records"
    )

    doctor = relationship(
        "Doctor",
        back_populates="medical_records"
    )

    appointment = relationship(
        "Appointment",
        back_populates="medical_record"
    )