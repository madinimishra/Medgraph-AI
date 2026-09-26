from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class PatientDocument(Base):

    __tablename__ = "patient_documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    hospital_id = Column(
        Integer,
        ForeignKey("hospital_documents.id"),
        nullable=False
    )

    hospital = relationship(
        "HospitalDocument",
        back_populates="patients"
    )

    medical_records = relationship(
        "MedicalRecordDocument",
        back_populates="patient"
    )