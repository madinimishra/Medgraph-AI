from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class DoctorDocument(Base):

    __tablename__ = "doctor_documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    department_id = Column(
        Integer,
        ForeignKey("department_documents.id"),
        nullable=False
    )

    department = relationship(
        "DepartmentDocument",
        back_populates="doctors"
    )

    medical_records = relationship(
        "MedicalRecordDocument",
        back_populates="doctor"
    )