from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class MedicalRecordDocument(Base):

    __tablename__ = "medical_record_documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    patient_id = Column(
        Integer,
        ForeignKey("patient_documents.id"),
        nullable=False
    )

    doctor_id = Column(
        Integer,
        ForeignKey("doctor_documents.id"),
        nullable=False
    )

    diagnosis = Column(
        Text,
        nullable=True
    )

    symptoms = Column(
        Text,
        nullable=True
    )

    medicines = Column(
        Text,
        nullable=True
    )

    lab_tests = Column(
        Text,
        nullable=True
    )

    follow_up = Column(
        Text,
        nullable=True
    )

    patient = relationship(
        "PatientDocument",
        back_populates="medical_records"
    )

    doctor = relationship(
        "DoctorDocument",
        back_populates="medical_records"
    )